"""Pinned Restic inventories for the dedicated PostgreSQL archive (no mutations)."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime

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


def snapshots(tag: str) -> list[dict]:
    items = json.loads(restic("snapshots", "--json", "--tag", tag, "--host", "printora-cloud"))
    if not items:
        raise ValueError("external_snapshot_absent")
    return sorted(items, key=lambda item: epoch(item["time"]), reverse=True)


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
