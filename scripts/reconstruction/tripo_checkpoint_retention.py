#!/usr/bin/env python3
"""Revisa e, sob confirmação explícita, remove checkpoints Tripo concluídos."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Sequence


CHECKPOINT_NAME = re.compile(r"^[0-9a-f]{64}\.json$")
CHECKPOINT_SCHEMA = "printora.tripo-checkpoint/v1"
MAX_CHECKPOINT_BYTES = 16 * 1024


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = review_checkpoints(
            args.state_dir,
            retention_days=args.retention_days,
            apply=args.apply,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, **report}, sort_keys=True))
    return 0


def review_checkpoints(
    state_dir: Path,
    *,
    retention_days: int = 30,
    apply: bool = False,
    now: datetime | None = None,
) -> dict[str, object]:
    root_input = state_dir.expanduser()
    if retention_days < 1 or retention_days > 3650:
        raise ValueError("retenção fora do limite")
    if not root_input.is_absolute() or not root_input.is_dir() or root_input.is_symlink():
        raise ValueError("diretório de checkpoint inválido")
    root = root_input.resolve()
    threshold = (now or datetime.now(UTC)) - timedelta(days=retention_days)
    candidates: list[str] = []
    removed: list[str] = []
    preserved = 0
    for path in sorted(root.iterdir()):
        if not CHECKPOINT_NAME.fullmatch(path.name):
            continue
        if not _is_expired_completed_checkpoint(path, threshold):
            preserved += 1
            continue
        candidates.append(path.name)
        if apply and _remove_under_lock(path, threshold):
            removed.append(path.name)
        elif apply:
            preserved += 1
    return {
        "mode": "apply" if apply else "preview",
        "retention_days": retention_days,
        "candidate_count": len(candidates),
        "removed_count": len(removed),
        "preserved_count": preserved,
        "candidates": candidates,
    }


def _is_expired_completed_checkpoint(path: Path, threshold: datetime) -> bool:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_CHECKPOINT_BYTES:
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        completed_at = datetime.fromisoformat(str(payload.get("completed_at", "")))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    return (
        payload.get("schema") == CHECKPOINT_SCHEMA
        and payload.get("status") == "completed"
        and completed_at.tzinfo is not None
        and completed_at.astimezone(UTC) < threshold
    )


def _remove_under_lock(path: Path, threshold: datetime) -> bool:
    lock_path = path.with_suffix(".lock")
    if lock_path.is_symlink():
        return False
    with lock_path.open("a+b") as lock:
        os.chmod(lock_path, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if not path.exists() or not _is_expired_completed_checkpoint(path, threshold):
            return False
        path.unlink()
        lock_path.unlink(missing_ok=True)
        return True


if __name__ == "__main__":
    raise SystemExit(main())
