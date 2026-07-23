from __future__ import annotations

import hashlib
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

from app.config import Settings, get_settings


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    size_bytes: int
    sha256: str
    content_type: str
    version_id: str | None = None
    etag: str | None = None
    path: Path | None = None


@dataclass(frozen=True)
class ObjectReader:
    body: BinaryIO
    size_bytes: int
    content_type: str


class ObjectStorage(Protocol):
    def write_quarantine(self, checksum: str, extension: str, body: bytes) -> StoredObject: ...

    def read_quarantine(self, key: str) -> bytes: ...

    def describe_quarantine(self, key: str, checksum: str, size_bytes: int, content_type: str) -> StoredObject: ...

    def promote(self, quarantined: StoredObject) -> StoredObject: ...

    def open_promoted(self, key: str) -> ObjectReader: ...


class LocalObjectStorage:
    def __init__(self, database_path: Path) -> None:
        self.root = database_path.parent / "library_uploads"

    def write_quarantine(self, checksum: str, extension: str, body: bytes) -> StoredObject:
        clean_extension = _clean_extension(extension)
        key = f"{checksum}{clean_extension}"
        path = self._safe_child("quarantine", key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return StoredObject(
            bucket="local-quarantine",
            key=key,
            path=path,
            size_bytes=len(body),
            sha256=checksum,
            content_type=_content_type(extension),
        )

    def promote(self, quarantined: StoredObject) -> StoredObject:
        if quarantined.path is None or not quarantined.path.is_file():
            raise FileNotFoundError("objeto em quarentena ausente")
        target = self._safe_child("objects", quarantined.key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(quarantined.path.read_bytes())
        return StoredObject(
            bucket="local-objects",
            key=quarantined.key,
            path=target,
            size_bytes=quarantined.size_bytes,
            sha256=quarantined.sha256,
            content_type=quarantined.content_type,
        )

    def open_promoted(self, key: str) -> ObjectReader:
        path = self._safe_child("objects", key)
        if not path.is_file():
            raise FileNotFoundError("objeto promovido ausente")
        return ObjectReader(body=path.open("rb"), size_bytes=path.stat().st_size, content_type=_content_type(path.suffix))

    def quarantine_path(self, key: str) -> Path:
        return self._safe_child("quarantine", key)

    def read_quarantine(self, key: str) -> bytes:
        path = self.quarantine_path(key)
        if not path.is_file():
            raise FileNotFoundError("arquivo de quarentena não encontrado")
        return path.read_bytes()

    def describe_quarantine(self, key: str, checksum: str, size_bytes: int, content_type: str) -> StoredObject:
        return StoredObject(
            bucket="local-quarantine",
            key=key,
            path=self.quarantine_path(key),
            size_bytes=size_bytes,
            sha256=checksum,
            content_type=content_type,
        )

    def _safe_child(self, *parts: str) -> Path:
        candidate = self.root.joinpath(*parts).resolve()
        root = self.root.resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("caminho de storage inválido")
        return candidate


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        missing = [
            name
            for name, value in (
                ("endpoint", settings.object_storage_endpoint_url),
                ("access key", settings.object_storage_access_key),
                ("secret key", settings.object_storage_secret_key),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("storage S3 incompleto: " + ", ".join(missing))
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise RuntimeError("dependência boto3 ausente para storage S3") from exc
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.object_storage_endpoint_url,
            region_name=settings.object_storage_region,
            aws_access_key_id=settings.object_storage_access_key,
            aws_secret_access_key=settings.object_storage_secret_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def write_quarantine(self, checksum: str, extension: str, body: bytes) -> StoredObject:
        if hashlib.sha256(body).hexdigest() != checksum:
            raise ValueError("checksum do upload divergente")
        key = _content_key(checksum, extension)
        content_type = _content_type(extension)
        response = self.client.put_object(
            Bucket=self.settings.object_storage_quarantine_bucket,
            Key=key,
            Body=body,
            ContentLength=len(body),
            ContentType=content_type,
            Metadata={"sha256": checksum},
        )
        return StoredObject(
            bucket=self.settings.object_storage_quarantine_bucket,
            key=key,
            size_bytes=len(body),
            sha256=checksum,
            content_type=content_type,
            version_id=response.get("VersionId"),
            etag=_clean_etag(response.get("ETag")),
        )

    def promote(self, quarantined: StoredObject) -> StoredObject:
        target_bucket = self.settings.object_storage_objects_bucket
        self.client.copy_object(
            Bucket=target_bucket,
            Key=quarantined.key,
            CopySource={"Bucket": quarantined.bucket, "Key": quarantined.key},
            ContentType=quarantined.content_type,
            Metadata={"sha256": quarantined.sha256},
            MetadataDirective="REPLACE",
        )
        head = self.client.head_object(Bucket=target_bucket, Key=quarantined.key)
        if int(head["ContentLength"]) != quarantined.size_bytes or head.get("Metadata", {}).get("sha256") != quarantined.sha256:
            raise RuntimeError("objeto promovido não reconciliou tamanho/checksum")
        return StoredObject(
            bucket=target_bucket,
            key=quarantined.key,
            size_bytes=quarantined.size_bytes,
            sha256=quarantined.sha256,
            content_type=head.get("ContentType") or quarantined.content_type,
            version_id=head.get("VersionId"),
            etag=_clean_etag(head.get("ETag")),
        )

    def read_quarantine(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.settings.object_storage_quarantine_bucket, Key=key)
        return response["Body"].read()

    def describe_quarantine(self, key: str, checksum: str, size_bytes: int, content_type: str) -> StoredObject:
        return StoredObject(
            bucket=self.settings.object_storage_quarantine_bucket,
            key=key,
            size_bytes=size_bytes,
            sha256=checksum,
            content_type=content_type,
        )

    def open_promoted(self, key: str) -> ObjectReader:
        response = self.client.get_object(Bucket=self.settings.object_storage_objects_bucket, Key=key)
        return ObjectReader(
            body=response["Body"],
            size_bytes=int(response["ContentLength"]),
            content_type=response.get("ContentType") or "application/octet-stream",
        )


def build_object_storage(database_path: Path, settings: Settings | None = None) -> ObjectStorage:
    resolved = settings or get_settings()
    runtime_profile = os.environ.get("PRINTORA_RUNTIME_PROFILE", "").strip().lower()
    if resolved.object_storage_mode == "s3":
        return S3ObjectStorage(resolved)
    if runtime_profile == "cloud":
        raise RuntimeError("perfil cloud exige PRINTORA_OBJECT_STORAGE_MODE=s3")
    return LocalObjectStorage(database_path)


def _content_key(checksum: str, extension: str) -> str:
    if len(checksum) != 64 or any(character not in "0123456789abcdef" for character in checksum):
        raise ValueError("checksum inválido")
    clean_extension = _clean_extension(extension)
    return f"sha256/{checksum[:2]}/{checksum}{clean_extension}"


def _clean_extension(extension: str) -> str:
    return extension.lower() if extension.startswith(".") and "/" not in extension and "\\" not in extension else ""


def _content_type(extension: str) -> str:
    return mimetypes.types_map.get(extension.lower(), "application/octet-stream")


def _clean_etag(value: str | None) -> str | None:
    return value.strip('"') if value else None
