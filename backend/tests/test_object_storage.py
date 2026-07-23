from __future__ import annotations

import hashlib
from io import BytesIO

import boto3
import pytest

from app.config import Settings
from app.object_storage import S3ObjectStorage, build_object_storage


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str, dict[str, str]]] = {}

    def put_object(self, **request):
        body = bytes(request["Body"])
        self.objects[(request["Bucket"], request["Key"])] = (body, request["ContentType"], request["Metadata"])
        return {"VersionId": "v1", "ETag": '"etag-1"'}

    def copy_object(self, **request):
        source = request["CopySource"]
        body, _, _ = self.objects[(source["Bucket"], source["Key"])]
        self.objects[(request["Bucket"], request["Key"])] = (body, request["ContentType"], request["Metadata"])
        return {"VersionId": "v2"}

    def head_object(self, **request):
        body, content_type, metadata = self.objects[(request["Bucket"], request["Key"])]
        return {"ContentLength": len(body), "ContentType": content_type, "Metadata": metadata, "VersionId": "v2", "ETag": '"etag-2"'}

    def get_object(self, **request):
        body, _, _ = self.objects[(request["Bucket"], request["Key"])]
        return {"Body": BytesIO(body)}


def test_s3_quarantine_and_promotion_reconcile_checksum(monkeypatch) -> None:
    client = FakeS3Client()
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)
    settings = Settings(
        object_storage_mode="s3",
        object_storage_endpoint_url="http://127.0.0.1:9100",
        object_storage_access_key="access",
        object_storage_secret_key="secret",
    )
    storage = S3ObjectStorage(settings)
    body = b"solid valid\nendsolid valid\n"
    checksum = hashlib.sha256(body).hexdigest()

    quarantined = storage.write_quarantine(checksum, ".stl", body)
    promoted = storage.promote(quarantined)

    assert quarantined.bucket == "printora-quarantine"
    assert quarantined.key == f"sha256/{checksum[:2]}/{checksum}.stl"
    assert storage.read_quarantine(quarantined.key) == body
    assert promoted.bucket == "printora-objects"
    assert promoted.sha256 == checksum
    assert promoted.version_id == "v2"


def test_cloud_profile_rejects_local_object_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_RUNTIME_PROFILE", "cloud")
    with pytest.raises(RuntimeError, match="perfil cloud exige"):
        build_object_storage(tmp_path / "printora.db", Settings(data_dir=tmp_path))
