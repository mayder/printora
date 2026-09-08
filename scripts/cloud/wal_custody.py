"""Pinned Restic inventories for the dedicated PostgreSQL archive (no mutations)."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from functools import lru_cache

ARCHIVE = "/var/lib/postgresql/16/printora-wal-archive"
WAL = re.compile(r"^[0-9A-F]{24}$")
SEGMENT_BYTES = 16 * 1024 * 1024


def epoch(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def restic(*args: str) -> str:
    result = subprocess.run(["restic", *args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise ValueError("restic_operation_failed")
    return result.stdout


@lru_cache(maxsize=1)
def _snapshot_index() -> list[dict]:
    # One immutable view per short-lived invocation; never persisted between runs.
    return json.loads(restic("snapshots", "--json", "--host", "printora-cloud"))


def snapshots(tag: str) -> list[dict]:
    items = [item for item in _snapshot_index() if tag in item.get("tags", [])]
    if not items:
        raise ValueError("external_snapshot_absent")
    return sorted(items, key=lambda item: epoch(item["time"]), reverse=True)


def restore_paths(snapshot: str, target: str, paths: list[str]) -> None:
    if not paths or any(path.rsplit("/", 1)[0] != ARCHIVE or not WAL.fullmatch(path.rsplit("/", 1)[1]) for path in paths):
        raise ValueError("restore_wal_paths_invalid")
    # Installed Restic supports repeated --include, not --include-file. Bound
    # argument size independently of archive age and the OS ARG_MAX limit.
    for offset in range(0, len(paths), 128):
        includes = [arg for path in paths[offset:offset + 128] for arg in ("--include", path)]
        restic("restore", snapshot, "--target", target, "--sparse", "--verify", *includes)


def inventory(snapshot: str) -> dict[str, dict]:
    nodes = [json.loads(line) for line in restic("ls", snapshot, "--json").splitlines()]
    return {node["path"]: node for node in nodes if node.get("type") == "file"}


def wal_nodes(nodes: dict[str, dict]) -> dict[str, dict]:
    return {
        path.rsplit("/", 1)[1]: node for path, node in nodes.items()
        if path.rsplit("/", 1)[0] == ARCHIVE and WAL.fullmatch(path.rsplit("/", 1)[1])
        and node.get("size") == SEGMENT_BYTES
    }


def ordinal(name: str) -> int:
    if not WAL.fullmatch(name) or int(name[16:], 16) >= 256:
        raise ValueError("wal_name_invalid")
    return int(name[8:16], 16) * 256 + int(name[16:], 16)


def required_names(first: str, last: str) -> list[str]:
    if first[:8] != last[:8] or ordinal(first) > ordinal(last):
        raise ValueError("timeline_or_range_unsupported")
    return [f"{first[:8]}{number // 256:08X}{number % 256:08X}"
            for number in range(ordinal(first), ordinal(last) + 1)]


def full_backup() -> tuple[dict, dict, dict]:
    snapshot = snapshots("printora-cloud-postgresql")[0]
    nodes = inventory(snapshot["id"])
    manifests = [path for path in nodes if path.endswith("/manifest.json")]
    if len(manifests) != 1:
        raise ValueError("full_manifest_ambiguous")
    manifest = json.loads(restic("dump", snapshot["id"], manifests[0]))
    if manifest.get("cluster") != "16/printora" or manifest.get("database") != "printora_cloud" or not manifest.get("recovery_custody_id"):
        raise ValueError("full_manifest_invalid")
    for suffix in ("/base/base.tar.zst", "/printora-postgresql.dump"):
        if not any(path.endswith(suffix) for path in nodes):
            raise ValueError("full_backup_incomplete")
    if not any(path.endswith(("/base/pg_wal.tar", "/base/pg_wal.tar.zst")) for path in nodes):
        raise ValueError("full_backup_wal_stream_absent")
    return snapshot, manifest, nodes


def first_backup_wal(snapshot: dict, nodes: dict) -> str:
    paths = [path for path in nodes if path.endswith("/base/backup_manifest")]
    if len(paths) != 1:
        raise ValueError("physical_manifest_absent_or_ambiguous")
    document = json.loads(restic("dump", snapshot["id"], paths[0]))
    ranges = document.get("WAL-Ranges", []) if isinstance(document, dict) else []
    if not isinstance(ranges, list) or len(ranges) != 1 or not isinstance(ranges[0], dict):
        raise ValueError("physical_wal_ranges_unsupported")
    item = ranges[0]
    timeline = item.get("Timeline")
    if type(timeline) is not int or not 0 < timeline <= 0xFFFFFFFF:
        raise ValueError("physical_timeline_invalid")
    positions = []
    for key in ("Start-LSN", "End-LSN"):
        value = item.get(key, "")
        if not isinstance(value, str) or not re.fullmatch(r"[0-9A-Fa-f]{1,8}/[0-9A-Fa-f]{1,8}", value):
            raise ValueError("physical_lsn_invalid")
        high, low = value.split("/")
        positions.append((int(high, 16) << 32) + int(low, 16))
    if positions[0] > positions[1]:
        raise ValueError("physical_lsn_range_invalid")
    number = positions[0] // SEGMENT_BYTES
    return f"{timeline:08X}{number // 256:08X}{number % 256:08X}"


def restore_plan(sync: dict, now: float) -> dict:
    if sync.get("status") != "passed" or not 0 <= now - epoch(sync["checked_at"]) <= 210:
        raise ValueError("restore_sync_state_invalid")
    full, manifest, nodes = full_backup()
    first = first_backup_wal(full, nodes)
    files = chain(first, sync["uploaded_wal"], full, nodes)
    return {"snapshot": full["id"], "manifest": manifest, "first_wal": first,
            "target_wal": sync["uploaded_wal"], "files": files}


def chain(first: str, last: str, full_snapshot: dict, full_nodes: dict) -> dict[str, str]:
    """Find historical snapshots even after local retention changes the latest tree."""
    required = set(required_names(first, last))
    found = {name: full_snapshot["id"] for name in wal_nodes(full_nodes) if name in required}
    history = snapshots("printora-cloud-wal")
    while required - found.keys():
        if not history:
            raise ValueError("external_chain_gap")
        snapshot = history.pop(0)
        nodes = wal_nodes(inventory(snapshot["id"]))
        for name in required & nodes.keys():
            found.setdefault(name, snapshot["id"])
        if not nodes:
            raise ValueError("external_wal_snapshot_empty")
        # A retained tree has a contiguous suffix. Jump to its first WAL's time,
        # then continue backwards; never infer presence from a snapshot timestamp.
        earliest = min(nodes, key=ordinal)
        if any(ordinal(name) >= ordinal(earliest) for name in required - found.keys()):
            raise ValueError("external_chain_gap")
        cutoff = epoch(nodes[earliest]["mtime"])
        history = [item for item in history if epoch(item["time"]) <= cutoff]
    return found
