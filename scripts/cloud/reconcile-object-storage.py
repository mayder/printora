#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.config import get_settings
from app.database import connect_database
from app.object_storage import S3ObjectStorage, StoredObject
from app.social_storage import SocialStorageRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcilia metadados canônicos e objetos S3 sem apagar conteúdo.")
    parser.add_argument("--adopt-prefix", help="adota objetos sintéticos sob este prefixo; não remove bytes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    repository = SocialStorageRepository(settings.database_path)
    storage = repository.storage
    if not isinstance(storage, S3ObjectStorage):
        raise RuntimeError("reconciliação exige adapter S3 ativo")
    run_id = create_run(settings.database_path)
    missing = 0
    corrupt = 0
    adopted = 0
    try:
        database_objects = load_database_objects(settings.database_path)
        for row in database_objects:
            try:
                head = storage.client.head_object(Bucket=row["bucket_name"], Key=row["object_key"])
            except Exception as exc:
                if _not_found(exc):
                    missing += 1
                    continue
                raise
            metadata_checksum = head.get("Metadata", {}).get("sha256")
            if int(head["ContentLength"]) != int(row["size_bytes"]) or (metadata_checksum and metadata_checksum != row["sha256"]):
                corrupt += 1

        bucket_objects = list_bucket_objects(storage, settings)
        known = {(str(row["bucket_name"]), str(row["object_key"])) for row in database_objects}
        orphans = [item for item in bucket_objects if (item["bucket"], item["key"]) not in known]
        if args.adopt_prefix:
            adopted = adopt_validation_objects(repository, orphans, args.adopt_prefix)
            database_objects = load_database_objects(settings.database_path)
            known = {(str(row["bucket_name"]), str(row["object_key"])) for row in database_objects}
            orphans = [item for item in bucket_objects if (item["bucket"], item["key"]) not in known]

        status = "passed" if missing == 0 and corrupt == 0 and not orphans else "failed"
        result = {
            "adopted_count": adopted,
            "database_count": len(database_objects),
            "bucket_count": len(bucket_objects),
            "orphan_keys_sha256": [hashlib.sha256(f'{item["bucket"]}/{item["key"]}'.encode()).hexdigest() for item in orphans],
            "content_deleted": False,
        }
        finish_run(settings.database_path, run_id, status, len(database_objects), missing, corrupt, len(orphans), result)
    except Exception as exc:
        finish_run(
            settings.database_path,
            run_id,
            "failed",
            0,
            missing,
            corrupt,
            0,
            {"error_type": type(exc).__name__, "content_deleted": False},
        )
        raise
    print(json.dumps({"status": status, "database": len(database_objects), "bucket": len(bucket_objects), "missing": missing, "corrupt": corrupt, "orphan": len(orphans), "adopted": adopted, "content_deleted": False}, sort_keys=True))
    if status != "passed":
        raise SystemExit(2)


def load_database_objects(database_path: Path):
    with connect_database(database_path) as connection:
        return connection.execute(
            "SELECT id, bucket_name, object_key, sha256, size_bytes, content_type, owner_user_id, state FROM cloud_objects ORDER BY id"
        ).fetchall()


def list_bucket_objects(storage: S3ObjectStorage, settings) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    for bucket in (
        settings.object_storage_quarantine_bucket,
        settings.object_storage_objects_bucket,
        settings.object_storage_artifacts_bucket,
    ):
        token = None
        while True:
            request = {"Bucket": bucket}
            if token:
                request["ContinuationToken"] = token
            response = storage.client.list_objects_v2(**request)
            objects.extend({"bucket": bucket, "key": item["Key"], "size": int(item["Size"])} for item in response.get("Contents", []))
            if not response.get("IsTruncated"):
                break
            token = response["NextContinuationToken"]
    return objects


def adopt_validation_objects(repository: SocialStorageRepository, orphans: list[dict[str, object]], prefix: str) -> int:
    settings = get_settings()
    with connect_database(settings.database_path) as connection:
        owner = connection.execute("SELECT id FROM auth_users ORDER BY id LIMIT 1").fetchone()
        if owner is None:
            raise RuntimeError("nenhum owner disponível para adoção")
        owner_id = int(owner["id"])
    adopted = 0
    for item in orphans:
        key = str(item["key"])
        if not key.startswith(prefix):
            continue
        checksum = Path(key).name.split(".", maxsplit=1)[0]
        if len(checksum) != 64 or any(character not in "0123456789abcdef" for character in checksum):
            continue
        stored = StoredObject(
            bucket=str(item["bucket"]),
            key=key,
            size_bytes=int(item["size"]),
            sha256=checksum,
            content_type="application/octet-stream",
        )
        reference_id = int(hashlib.sha256(f'{item["bucket"]}/{key}'.encode()).hexdigest()[:15], 16)
        with connect_database(settings.database_path) as connection:
            repository.register_object(
                connection,
                stored,
                owner_user_id=owner_id,
                reference_type="storage_validation_probe",
                reference_id=reference_id,
                state="promoted" if item["bucket"] == settings.object_storage_objects_bucket else "quarantined",
            )
        adopted += 1
    return adopted


def create_run(database_path: Path) -> int:
    with connect_database(database_path) as connection:
        cursor = connection.execute("INSERT INTO cloud_object_reconciliation_runs (mode) VALUES ('integrity')")
        return int(cursor.lastrowid)


def finish_run(database_path: Path, run_id: int, status: str, scanned: int, missing: int, corrupt: int, orphan: int, result: dict[str, object]) -> None:
    with connect_database(database_path) as connection:
        connection.execute(
            """
            UPDATE cloud_object_reconciliation_runs
            SET status = ?, scanned_count = ?, missing_count = ?, corrupt_count = ?,
                orphan_count = ?, result_json = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, scanned, missing, corrupt, orphan, json.dumps(result, sort_keys=True), run_id),
        )


def _not_found(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    return response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}


if __name__ == "__main__":
    main()
