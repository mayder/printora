#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import get_settings
from app.database import connect_database
from app.object_storage import S3ObjectStorage
from app.social_storage import SocialStorageRepository


@dataclass(frozen=True)
class ManifestEntry:
    reference_type: str
    reference_id: int
    owner_user_id: int
    file_name: str
    source_key: str
    size_bytes: int
    sha256: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migra objetos locais para o storage S3 sem remover a origem.")
    parser.add_argument("--apply", action="store_true", help="grava objetos e metadados; sem esta flag executa dry-run")
    parser.add_argument("--manifest", type=Path, help="grava o manifesto JSON sem credenciais ou paths absolutos")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    repository = SocialStorageRepository(settings.database_path)
    if not isinstance(repository.storage, S3ObjectStorage):
        raise RuntimeError("migração exige adapter S3 ativo")
    source_root = (settings.database_path.parent / "library_uploads" / "quarantine").resolve()
    entries = load_manifest_entries(settings.database_path)
    manifest = {
        "mode": "apply" if args.apply else "dry_run",
        "source_retained": True,
        "entry_count": len(entries),
        "entries": [asdict(entry) for entry in entries],
    }
    if args.manifest:
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        args.manifest.chmod(0o600)

    migrated = 0
    missing = 0
    corrupt = 0
    run_id = create_reconciliation_run(settings.database_path, "incremental" if args.apply else "manifest")
    try:
        for entry in entries:
            source = safe_source(source_root, entry.source_key)
            if not source.is_file():
                missing += 1
                continue
            body = source.read_bytes()
            if len(body) != entry.size_bytes or hashlib.sha256(body).hexdigest() != entry.sha256:
                corrupt += 1
                continue
            if not args.apply:
                continue
            stored = repository.storage.write_quarantine(entry.sha256, Path(entry.file_name).suffix.lower(), body)
            with connect_database(settings.database_path) as connection:
                repository.register_object(
                    connection,
                    stored,
                    owner_user_id=entry.owner_user_id,
                    reference_type=entry.reference_type,
                    reference_id=entry.reference_id,
                    state=entry.status if entry.status in {"quarantined", "rejected", "analyzed"} else "quarantined",
                )
            migrated += 1
        status = "passed" if missing == 0 and corrupt == 0 else "failed"
        finish_reconciliation_run(
            settings.database_path,
            run_id,
            status=status,
            scanned=len(entries),
            missing=missing,
            corrupt=corrupt,
            result={"migrated_count": migrated, "source_retained": True},
        )
    except Exception as exc:
        finish_reconciliation_run(
            settings.database_path,
            run_id,
            status="failed",
            scanned=len(entries),
            missing=missing,
            corrupt=corrupt,
            result={"error_type": type(exc).__name__, "migrated_count": migrated, "source_retained": True},
        )
        raise
    print(json.dumps({"status": status, "scanned": len(entries), "migrated": migrated, "missing": missing, "corrupt": corrupt, "source_retained": True}, sort_keys=True))


def load_manifest_entries(database_path: Path) -> list[ManifestEntry]:
    with connect_database(database_path) as connection:
        rows = connection.execute(
            """
            SELECT 'social_library_file' AS reference_type, lf.id AS reference_id,
                   li.owner_user_id, lf.file_name, lf.quarantine_key AS source_key,
                   COALESCE(lf.uploaded_size_bytes, lf.size_bytes, 0) AS size_bytes,
                   lf.sha256, lf.validation_status AS status
            FROM social_library_files lf
            JOIN social_library_items li ON li.id = lf.item_id
            WHERE lf.quarantine_key IS NOT NULL AND lf.sha256 IS NOT NULL
            UNION ALL
            SELECT 'print_project_file', pf.id, pp.owner_user_id, pf.file_name,
                   pf.quarantine_key, COALESCE(pf.uploaded_size_bytes, pf.size_bytes, 0),
                   pf.sha256, pf.validation_status
            FROM print_project_files pf
            JOIN print_projects pp ON pp.id = pf.project_id
            WHERE pf.quarantine_key IS NOT NULL AND pf.sha256 IS NOT NULL
              AND pp.owner_user_id IS NOT NULL
            ORDER BY reference_type, reference_id
            """
        ).fetchall()
    return [
        ManifestEntry(
            reference_type=str(row["reference_type"]),
            reference_id=int(row["reference_id"]),
            owner_user_id=int(row["owner_user_id"]),
            file_name=str(row["file_name"]),
            source_key=str(row["source_key"]),
            size_bytes=int(row["size_bytes"]),
            sha256=str(row["sha256"]),
            status=str(row["status"]),
        )
        for row in rows
    ]


def safe_source(root: Path, key: str) -> Path:
    candidate = root.joinpath(key).resolve()
    if root not in candidate.parents:
        raise ValueError("chave local fora da quarentena")
    return candidate


def create_reconciliation_run(database_path: Path, mode: str) -> int:
    with connect_database(database_path) as connection:
        cursor = connection.execute("INSERT INTO cloud_object_reconciliation_runs (mode) VALUES (?)", (mode,))
        return int(cursor.lastrowid)


def finish_reconciliation_run(
    database_path: Path,
    run_id: int,
    *,
    status: str,
    scanned: int,
    missing: int,
    corrupt: int,
    result: dict[str, object],
) -> None:
    with connect_database(database_path) as connection:
        connection.execute(
            """
            UPDATE cloud_object_reconciliation_runs
            SET status = ?, scanned_count = ?, missing_count = ?, corrupt_count = ?,
                result_json = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, scanned, missing, corrupt, json.dumps(result, sort_keys=True), run_id),
        )


if __name__ == "__main__":
    main()
