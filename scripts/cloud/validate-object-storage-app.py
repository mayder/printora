#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid

from app.config import get_settings
from app.database import connect_database
from app.object_storage import S3ObjectStorage
from app.social_storage import SocialStorageRepository


def main() -> None:
    settings = get_settings()
    storage_repository = SocialStorageRepository(settings.database_path)
    storage = storage_repository.storage
    if not isinstance(storage, S3ObjectStorage):
        raise RuntimeError("perfil cloud não resolveu o adapter S3")

    probe_size_mib = int(os.environ.get("PRINTORA_STORAGE_PROBE_SIZE_MIB", "0"))
    if probe_size_mib < 0 or probe_size_mib > 25:
        raise RuntimeError("tamanho da prova deve permanecer entre 0 e 25 MiB")
    seed = f"printora-storage-proof:{uuid.uuid4()}".encode()
    body = (
        (seed * ((probe_size_mib * 1024 * 1024 + len(seed) - 1) // len(seed)))[
            : probe_size_mib * 1024 * 1024
        ]
        if probe_size_mib
        else seed
    )
    checksum = hashlib.sha256(body).hexdigest()
    quarantined = storage.write_quarantine(checksum, ".probe", body)
    if hashlib.sha256(storage.read_quarantine(quarantined.key)).hexdigest() != checksum:
        raise RuntimeError("leitura da quarentena divergiu do checksum")
    promoted = storage.promote(quarantined)
    reference_id = time.time_ns()

    with connect_database(settings.database_path) as connection:
        owner = connection.execute("SELECT id FROM auth_users ORDER BY id LIMIT 1").fetchone()
        if owner is None:
            raise RuntimeError("nenhum owner disponível para a prova")
        owner_id = int(owner["id"])
        quarantine_id = storage_repository.register_object(
            connection,
            quarantined,
            owner_user_id=owner_id,
            reference_type="storage_probe_quarantine",
            reference_id=reference_id,
            state="quarantined",
        )
        promoted_id = storage_repository.register_object(
            connection,
            promoted,
            owner_user_id=owner_id,
            reference_type="storage_probe_promoted",
            reference_id=reference_id,
            state="promoted",
        )

    print(
        json.dumps(
            {
                "adapter": "s3",
                "checksum_match": True,
                "quarantine_object_id": quarantine_id,
                "promoted_object_id": promoted_id,
                "size_bytes": len(body),
                "runtime_profile": os.environ.get("PRINTORA_RUNTIME_PROFILE"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
