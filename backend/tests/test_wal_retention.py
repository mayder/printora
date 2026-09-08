from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
import wal_custody as custody

spec = importlib.util.spec_from_file_location("wal_retention", ROOT / "scripts/cloud/retain-postgresql-wal.py")
retention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retention)


def wal(number):
    return f"0000000100000000{number:08X}"


def test_required_chain_crosses_log_boundary():
    assert custody.required_names("0000000100000000000000FF", "000000010000000100000001") == [
        "0000000100000000000000FF", "000000010000000100000000", "000000010000000100000001"]


@pytest.mark.parametrize("first,last", [(wal(3), wal(1)), (wal(1), "000000020000000000000002"), (wal(256), wal(257))])
def test_reject_unsupported_chain(first, last):
    with pytest.raises(ValueError):
        custody.required_names(first, last)


@pytest.mark.parametrize("free", [0, 9, 15, 20])
def test_pressure_never_reduces_72_hour_margin_or_removes_newest(free):
    now = 1_000_000
    files = {wal(1): SimpleNamespace(st_size=16, st_mtime=now - 73 * 3600),
             wal(2): SimpleNamespace(st_size=16, st_mtime=now - 72 * 3600),
             wal(3): SimpleNamespace(st_size=16, st_mtime=now - 80 * 3600)}
    assert retention.candidates(files, now, free) == [wal(1)]


def test_normal_retention_uses_seven_days_and_capacity_uses_72_hours(monkeypatch):
    now = 1_000_000
    files = {wal(1): SimpleNamespace(st_size=10, st_mtime=now - 169 * 3600),
             wal(2): SimpleNamespace(st_size=10, st_mtime=now - 80 * 3600),
             wal(3): SimpleNamespace(st_size=10, st_mtime=now)}
    assert retention.candidates(files, now, 50) == [wal(1)]
    monkeypatch.setattr(retention, "MAX_ARCHIVE_BYTES", 20)
    assert retention.candidates(files, now, 50) == [wal(1), wal(2)]


def test_inventory_excludes_partial_wrong_path_and_wrong_size():
    names = {f"{custody.ARCHIVE}/{wal(1)}": {"size": custody.SEGMENT_BYTES},
             f"{custody.ARCHIVE}/{wal(2)}.partial": {"size": custody.SEGMENT_BYTES},
             f"/pg_wal/{wal(3)}": {"size": custody.SEGMENT_BYTES},
             f"{custody.ARCHIVE}/{wal(4)}": {"size": 1}}
    assert list(custody.wal_nodes(names)) == [wal(1)]


def test_chain_recovers_across_historical_snapshots(monkeypatch):
    history = [{"id": "new", "time": "2026-09-08T00:00:00Z"},
               {"id": "old", "time": "2026-09-04T00:00:00Z"}]
    monkeypatch.setattr(custody, "snapshots", lambda _: history.copy())
    def inventory(snapshot):
        return {f"{custody.ARCHIVE}/{wal(i)}": {"size": custody.SEGMENT_BYTES,
                    "mtime": "2026-09-05T00:00:00Z"} for i in ([3, 4] if snapshot == "new" else [1, 2, 3])}
    monkeypatch.setattr(custody, "inventory", inventory)
    assert custody.chain(wal(1), wal(4), {"id": "base"}, {}) == {
        wal(1): "old", wal(2): "old", wal(3): "new", wal(4): "new"}


def test_chain_gap_fails_closed(monkeypatch):
    monkeypatch.setattr(custody, "snapshots", lambda _: [{"id": "new", "time": "2026-09-08T00:00:00Z"}])
    monkeypatch.setattr(custody, "inventory", lambda _: {
        f"{custody.ARCHIVE}/{wal(i)}": {"size": custody.SEGMENT_BYTES, "mtime": "2026-09-05T00:00:00Z"} for i in [1, 3]})
    with pytest.raises(ValueError, match="external_chain_gap"):
        custody.chain(wal(1), wal(3), {"id": "base"}, {})


@pytest.mark.parametrize("timestamp,status", [(0, "passed"), (1001, "passed"), (999, "failed")])
def test_invalid_sync_state_blocks(monkeypatch, tmp_path, timestamp, status):
    monkeypatch.setattr(retention, "STATE", tmp_path)
    monkeypatch.setattr(retention, "epoch", lambda _: timestamp)
    (tmp_path / "wal-sync.json").write_text(json.dumps({"status": status, "checked_at": "test"}))
    with pytest.raises(ValueError):
        retention.read_state("wal-sync.json", 210, 1000)


def test_wrong_archive_path_never_traversed(tmp_path):
    with pytest.raises(ValueError, match="archive_path_invalid"):
        retention.local_files(tmp_path)


def test_checksum_mismatch_blocks_before_delete(monkeypatch, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / wal(1)).write_bytes(b"a")
    restored = tmp_path / custody.ARCHIVE.lstrip("/")
    restored.mkdir(parents=True)
    (restored / wal(1)).write_bytes(b"b")
    monkeypatch.setattr(retention, "SEGMENT_BYTES", 1)
    monkeypatch.setattr(retention, "restic", lambda *args: "")
    with pytest.raises(ValueError, match="wal_checksum_mismatch"):
        retention.verify_batch([wal(1)], {wal(1): "snapshot"}, tmp_path, source)
    assert (source / wal(1)).read_bytes() == b"a"


def test_shared_lock_is_stable_and_units_are_installed():
    sync = (ROOT / "scripts/cloud/sync-postgresql-wal.sh").read_text()
    assert str(retention.LOCK) in sync
    for script in ["deploy-blue-green.sh", "bootstrap-blue-green.sh"]:
        text = (ROOT / "scripts/cloud" / script).read_text()
        assert "printora-cloud-wal-retention.service" in text
        assert "systemctl enable --now printora-cloud-wal-retention.timer" in text
    unit = (ROOT / "packaging/systemd/printora-cloud-wal-retention.service").read_text()
    assert "InaccessiblePaths=/var/lib/postgresql/16/printora/pg_wal" in unit


@pytest.mark.parametrize("free,expected", [(0, False), (9, False), (10, True), (20, True)])
def test_disk_intensive_operations_have_ten_percent_gate(free, expected):
    from capacity_guard import allowed
    assert allowed(100, free) == expected
    assert not allowed(0, 0)


def test_changed_file_aborts_whole_batch_before_any_delete(monkeypatch, tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    first = root / wal(1)
    second = root / wal(2)
    first.write_text("before")
    second.write_text("before")
    selected = {wal(1): first.stat(), wal(2): second.stat()}
    first.write_text("changed")
    monkeypatch.setattr(retention, "LOCK", tmp_path / "lock")
    monkeypatch.setattr(retention, "read_state", lambda *args: {})
    monkeypatch.setattr(retention, "local_files", lambda _: {wal(1): first.stat(), wal(2): second.stat()})
    with pytest.raises(ValueError, match="wal_changed_after_verification"):
        retention.apply_batch(root, selected, {}, 1_000_000)
    assert first.exists() and second.exists()


def test_successful_batch_persists_proof_and_keeps_latest(monkeypatch, tmp_path):
    import os
    root = tmp_path / "archive"
    root.mkdir()
    first = root / wal(1)
    second = root / wal(2)
    first.write_text("old")
    second.write_text("latest")
    os.utime(first, (1, 1))
    monkeypatch.setattr(retention, "LOCK", tmp_path / "lock")
    monkeypatch.setattr(retention, "STATE", tmp_path)
    monkeypatch.setattr(retention, "read_state", lambda *args: {})
    monkeypatch.setattr(retention, "local_files", lambda _: {wal(1): first.stat(), wal(2): second.stat()})
    retention.apply_batch(root, {wal(1): first.stat()}, {wal(1): {"sha256": "verified", "snapshot": "pinned"}}, 1_000_000)
    assert not first.exists() and second.exists()
    evidence = next((tmp_path / "wal-retention").glob("*.jsonl")).read_text()
    assert '"delete_intent"' in evidence and '"deleted"' in evidence and '"pinned"' in evidence


def test_full_backup_requires_its_initial_wal_stream(monkeypatch):
    monkeypatch.setattr(custody, "snapshots", lambda _: [{"id": "full"}])
    nodes = {"/tmp/backup/manifest.json": {}, "/tmp/backup/base/base.tar.zst": {},
             "/tmp/backup/printora-postgresql.dump": {}}
    monkeypatch.setattr(custody, "inventory", lambda _: nodes)
    monkeypatch.setattr(custody, "restic", lambda *args: json.dumps({
        "cluster": "16/printora", "database": "printora_cloud", "recovery_custody_id": "test"}))
    with pytest.raises(ValueError, match="full_backup_wal_stream_absent"):
        custody.full_backup()
    nodes["/tmp/backup/base/pg_wal.tar.zst"] = {}
    assert custody.full_backup()[0]["id"] == "full"
