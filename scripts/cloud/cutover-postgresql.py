#!/usr/bin/env python3
"""Executa cutover com lock de escrita SQLite e catch-up final da outbox."""

from __future__ import annotations

import argparse
import importlib.util
import os
import pwd
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


BASE_PATH = Path(os.environ.get("PRINTORA_BASE_PATH", "/var/www/print3dmaker.xyz"))
SQLITE_PATH = BASE_PATH / "shared/data/printora.db"
ACTIVE_SLOT_FILE = BASE_PATH / "shared/active-slot"
NGINX_LINK = Path("/etc/nginx/conf.d/printora-cloud-active.conf")
CONFIRMATION = "CONFIRMAR-CUTOVER-POSTGRESQL"


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, capture_output=True, text=True)


def slot_port(slot: str) -> int:
    return 8069 if slot == "blue" else 8070


def other_slot(slot: str) -> str:
    return "green" if slot == "blue" else "blue"


def probe(port: int, path: str) -> None:
    run("curl", "--max-time", "5", "-fsS", f"http://127.0.0.1:{port}{path}")


def load_replicator(release_dir: Path) -> Any:
    script = release_dir / "scripts/cloud/replicate-sqlite-outbox.py"
    spec = importlib.util.spec_from_file_location("printora_transition_replicator", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("replicador de transição ausente")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def catch_up_under_lock(
    source: sqlite3.Connection,
    postgresql_url: str,
    replicator: Any,
) -> int:
    final_watermark = int(
        source.execute(
            "SELECT COALESCE(MAX(id), 0) FROM postgresql_transition_outbox"
        ).fetchone()[0]
    )
    with psycopg.connect(postgresql_url, row_factory=dict_row) as target:
        shapes = replicator.load_shapes(target)
        while True:
            processed, watermark = replicator.replicate_batch(source, target, shapes, 500)
            target.commit()
            if watermark >= final_watermark:
                break
            if processed == 0:
                raise RuntimeError("replicação parou antes do watermark final")
        replicator.sync_sequences(target)
        target.commit()
        persisted = target.execute(
            "SELECT watermark FROM printora_transition_replication_state WHERE id = 1"
        ).fetchone()
        if persisted is None or int(persisted["watermark"]) != final_watermark:
            raise RuntimeError("watermark PostgreSQL não alcançou a origem bloqueada")
    return final_watermark


def switch_traffic(candidate_slot: str, source_slot: str, release_dir: Path) -> None:
    candidate_upstream = BASE_PATH / f"shared/nginx/upstream-{candidate_slot}.conf"
    previous_upstream = os.readlink(NGINX_LINK)
    temporary_link = NGINX_LINK.with_name(NGINX_LINK.name + ".next")
    temporary_link.unlink(missing_ok=True)
    temporary_link.symlink_to(candidate_upstream)
    os.replace(temporary_link, NGINX_LINK)
    try:
        run("nginx", "-t")
    except Exception:
        NGINX_LINK.unlink(missing_ok=True)
        NGINX_LINK.symlink_to(previous_upstream)
        raise
    run("systemctl", "reload", "nginx")
    service = f"printora-cloud@{source_slot}.service"
    stopped = run("systemctl", "stop", service, check=False)
    if stopped.returncode != 0:
        run("systemctl", "kill", "--kill-whom=all", service, check=False)
    if run("systemctl", "is-active", "--quiet", service, check=False).returncode == 0:
        raise RuntimeError("slot SQLite permaneceu ativo após a troca")
    ACTIVE_SLOT_FILE.write_text(candidate_slot + "\n", encoding="utf-8")
    current_next = BASE_PATH / "current.next"
    current_next.unlink(missing_ok=True)
    current_next.symlink_to(release_dir)
    os.replace(current_next, BASE_PATH / "current")


def prepare_postgresql_standby(source_slot: str, release_dir: Path, candidate_slot: str) -> None:
    source_env = BASE_PATH / f"shared/slots/{source_slot}.env"
    candidate_env = (BASE_PATH / f"shared/slots/{candidate_slot}.env").read_text(encoding="utf-8")
    candidate_port = slot_port(candidate_slot)
    source_port = slot_port(source_slot)
    source_env.write_text(
        candidate_env.replace(f"PRINTORA_PORT={candidate_port}", f"PRINTORA_PORT={source_port}")
        .replace(f"PRINTORA_SLOT={candidate_slot}", f"PRINTORA_SLOT={source_slot}"),
        encoding="utf-8",
    )
    deploy = pwd.getpwnam("deploy")
    os.chown(source_env, deploy.pw_uid, deploy.pw_gid)
    source_env.chmod(0o640)
    source_link = BASE_PATH / f"slots/{source_slot}"
    source_next = BASE_PATH / f"slots/{source_slot}.next"
    source_next.unlink(missing_ok=True)
    source_next.symlink_to(release_dir)
    os.replace(source_next, source_link)
    run("systemctl", "restart", f"printora-cloud@{source_slot}.service")
    for _attempt in range(60):
        try:
            probe(source_port, "/ready")
            return
        except subprocess.CalledProcessError:
            time.sleep(1)
    raise RuntimeError("standby PostgreSQL não ficou ready")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_sha")
    parser.add_argument("confirmation")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("cutover exige root")
    if args.confirmation != CONFIRMATION:
        raise SystemExit("confirmação de cutover inválida")
    if not 7 <= len(args.release_sha) <= 64 or any(
        char not in "0123456789abcdef" for char in args.release_sha
    ):
        raise SystemExit("SHA de release inválido")

    source_slot = ACTIVE_SLOT_FILE.read_text(encoding="utf-8").strip()
    if source_slot not in {"blue", "green"}:
        raise SystemExit("slot ativo inválido")
    candidate_slot = other_slot(source_slot)
    candidate_port = slot_port(candidate_slot)
    release_dir = (BASE_PATH / f"releases/{args.release_sha}").resolve()
    if (BASE_PATH / f"slots/{candidate_slot}").resolve() != release_dir:
        raise SystemExit("canário não aponta para a release confirmada")
    probe(candidate_port, "/ready")
    probe(candidate_port, "/health")
    probe(candidate_port, "/api/catalog")

    postgresql_url = os.environ.get("PRINTORA_DATABASE_URL", "").strip()
    if not postgresql_url.startswith("postgresql://"):
        raise SystemExit("PRINTORA_DATABASE_URL PostgreSQL ausente")
    replicator = load_replicator(release_dir)
    source = sqlite3.connect(SQLITE_PATH, timeout=60, isolation_level=None)
    source.row_factory = sqlite3.Row
    try:
        source.execute("PRAGMA busy_timeout = 60000")
        source.execute("BEGIN IMMEDIATE")
        watermark = catch_up_under_lock(source, postgresql_url, replicator)
        switch_traffic(candidate_slot, source_slot, release_dir)
        source.rollback()
    except Exception:
        source.rollback()
        raise
    finally:
        source.close()

    prepare_postgresql_standby(source_slot, release_dir, candidate_slot)
    print(
        f"active_slot={candidate_slot} standby_slot={source_slot} "
        f"backend=postgresql watermark={watermark} data_restored=false"
    )


if __name__ == "__main__":
    main()
