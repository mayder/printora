#!/usr/bin/env python3
"""Fail-closed local WAL retention. External snapshots are never deleted."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path

from wal_custody import ARCHIVE, SEGMENT_BYTES, WAL, chain, epoch, full_backup, inventory, restic, snapshots, wal_nodes

STATE = Path("/var/lib/printora-cloud/recovery")
LOCK = Path("/var/lib/printora-cloud/recovery/wal-sync.lock")
MIN_HOURS = 72
MAX_HOURS = 168
MAX_ARCHIVE_BYTES = 64 * 1024**3
BATCH_SIZE = 32


def emit(event: str, **values) -> None:
    print(json.dumps({"event": event, **values}, sort_keys=True), flush=True)


def read_state(name: str, maximum_age: int, now: float) -> dict:
    data = json.loads((STATE / name).read_text())
    timestamp = data.get("checked_at", data.get("completed_at", ""))
    if data.get("status") != "passed" or not 0 <= now - epoch(timestamp) <= maximum_age:
        raise ValueError("recovery_state_stale_or_invalid")
    return data


def local_files(root: Path) -> dict[str, os.stat_result]:
    if str(root) != ARCHIVE or root.resolve() != root or root.is_symlink():
        raise ValueError("archive_path_invalid")
    result = {}
    for path in root.iterdir():
        info = path.lstat()
        if WAL.fullmatch(path.name):
            if not stat.S_ISREG(info.st_mode) or info.st_size != SEGMENT_BYTES or info.st_nlink != 1:
                raise ValueError("wal_file_invalid")
            result[path.name] = info
    if not result:
        raise ValueError("archive_empty")
    return result


def candidates(files: dict, now: float, free_percent: float) -> list[str]:
    newest = {max(files), max(files, key=lambda name: files[name].st_mtime)}
    size = sum(info.st_size for info in files.values())
    pressure = free_percent <= 20 or size > MAX_ARCHIVE_BYTES
    cutoff = now - (MIN_HOURS if pressure else MAX_HOURS) * 3600
    return sorted(name for name, info in files.items()
                  if name not in newest and info.st_mtime < cutoff)


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def verify_batch(names: list[str], custody: dict[str, str], target: Path, root: Path) -> dict:
    proofs = {}
    for snapshot in sorted({custody[name] for name in names}):
        includes = target / "includes.txt"
        includes.write_text("\n".join(f"{ARCHIVE}/{name}" for name in names if custody[name] == snapshot) + "\n")
        restic("restore", snapshot, "--target", str(target), "--sparse", "--verify", "--include-file", str(includes))
    for name in names:
        restored = target / ARCHIVE.lstrip("/") / name
        if not restored.is_file() or restored.stat().st_size != SEGMENT_BYTES:
            raise ValueError("restored_wal_absent")
        external_hash = digest(restored)
        if external_hash != digest(root / name):
            raise ValueError("wal_checksum_mismatch")
        proofs[name] = {"snapshot": custody[name], "sha256": external_hash}
    return proofs


def health() -> None:
    command = ["runuser", "-u", "postgres", "--", "psql", "-p", "5433", "-d", "printora_cloud", "-X", "-Atqc", "SELECT NOT pg_is_in_recovery()"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    if result.returncode or result.stdout.strip() != "t":
        raise ValueError("postgresql_not_ready")
    slot = Path("/var/www/print3dmaker.xyz/shared/active-slot").read_text().strip()
    if slot not in {"blue", "green"}:
        raise ValueError("active_slot_invalid")
    for port in ((8069 if slot == "blue" else 8070), 8071):
        subprocess.run(["curl", "-fsS", "--max-time", "5", f"http://127.0.0.1:{port}/ready"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def apply_batch(root: Path, selected: dict, proofs: dict, now: float) -> None:
    # The synchronization uses this same persistent inode in the root-owned state
    # directory; RuntimeDirectory cleanup cannot replace it. Expensive external reads happen before the short lock.
    LOCK.parent.mkdir(mode=0o700, exist_ok=True)
    with LOCK.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        read_state("wal-sync.json", 210, time.time())
        current = local_files(root)
        for name, before in selected.items():
            after = current.get(name)
            if after is None or (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError("wal_changed_after_verification")
            if name in {max(current), max(current, key=lambda item: current[item].st_mtime)} or after.st_mtime >= now - MIN_HOURS * 3600:
                raise ValueError("local_margin_violation")
        evidence = STATE / "wal-retention"
        evidence.mkdir(mode=0o700, exist_ok=True)
        record = evidence / f"{time.time_ns()}.jsonl"
        with record.open("x") as output:
            for name, before in selected.items():
                output.write(json.dumps({"event": "delete_intent", "name": name, "mtime": before.st_mtime,
                                         "cutoff": now - MIN_HOURS * 3600, **proofs[name]}) + "\n")
            output.flush()
            os.fsync(output.fileno())
            evidence_fd = os.open(evidence, os.O_DIRECTORY)
            try:
                os.fsync(evidence_fd)
            finally:
                os.close(evidence_fd)
            for name in selected:
                (root / name).unlink()
                output.write(json.dumps({"event": "deleted", "name": name, "at": time.time()}) + "\n")
                output.flush()
                os.fsync(output.fileno())
        directory = os.open(root, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def run(apply: bool) -> None:
    now = time.time()
    root = Path(ARCHIVE)
    files = local_files(root)
    sync = read_state("wal-sync.json", 210, now)
    read_state("full-backup.json", 7 * 86400, now)
    read_state("restore-test.json", 648000, now)
    full, manifest, full_nodes = full_backup()
    if not 0 <= now - epoch(full["time"]) <= 7 * 86400:
        raise ValueError("external_full_backup_stale")
    latest = snapshots("printora-cloud-wal")[0]
    nodes = wal_nodes(inventory(latest["id"]))
    if sync["uploaded_wal"] not in nodes:
        raise ValueError("sync_snapshot_mismatch")
    custody = chain(manifest["last_archived_wal"], sync["uploaded_wal"], full, full_nodes)
    # Older than the base still requires individually verified external custody.
    custody.update({name: latest["id"] for name in nodes})
    usage = shutil.disk_usage(root)
    free = usage.free * 100 / usage.total
    names = candidates(files, now, free)
    if any(name not in custody for name in names):
        raise ValueError("candidate_external_custody_absent")
    emit("wal_retention_plan", candidates=len(names), free_percent=round(free, 2), minimum_hours=MIN_HOURS, apply=apply)
    if not apply or not names:
        return
    health()
    # One bounded batch per invocation; timers converge without delaying RPO sync.
    names = names[:BATCH_SIZE]
    temporary_root = Path("/run/printora-wal-retention")
    temporary_root.mkdir(mode=0o700, exist_ok=True)
    if shutil.disk_usage(temporary_root).free < (BATCH_SIZE + 4) * SEGMENT_BYTES:
        raise ValueError("verification_capacity_insufficient")
    with tempfile.TemporaryDirectory(prefix="printora-wal-verify-", dir=temporary_root) as temporary:
        proofs = verify_batch(names, custody, Path(temporary), root)
        apply_batch(root, {name: files[name] for name in names}, proofs, now)
    health()
    usage = shutil.disk_usage(root)
    emit("wal_retention_completed", removed=len(names), bytes=len(names) * SEGMENT_BYTES,
         free_bytes=usage.free, free_percent=round(usage.free * 100 / usage.total, 2))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0:
        emit("wal_retention_failed", reason="root_required")
        return 1
    try:
        run(args.apply)
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError):
        emit("wal_retention_failed", reason="custody_state_capacity_or_health_invalid")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
