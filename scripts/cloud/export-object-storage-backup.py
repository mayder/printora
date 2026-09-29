#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.config import Config


BUCKETS = ("printora-quarantine", "printora-objects", "printora-artifacts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exporta todas as versões S3 para backup externo criptografado.")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_user = os.environ.get("MINIO_ROOT_USER", "")
    root_password = os.environ.get("MINIO_ROOT_PASSWORD", "")
    if not root_user or not root_password:
        raise RuntimeError("credencial root do storage ausente")
    args.output.mkdir(parents=True, exist_ok=False)
    content_root = args.output / "objects"
    content_root.mkdir(mode=0o700)
    client = boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:9100",
        region_name="us-east-1",
        aws_access_key_id=root_user,
        aws_secret_access_key=root_password,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    entries: list[dict[str, object]] = []
    for bucket in BUCKETS:
        for version in list_versions(client, bucket):
            key = str(version["Key"])
            version_id = str(version["VersionId"])
            if version["kind"] == "delete_marker":
                entries.append(
                    {
                        "bucket": bucket,
                        "key": key,
                        "version_id": version_id,
                        "kind": "delete_marker",
                        "last_modified": version["LastModified"].astimezone(timezone.utc).isoformat(),
                    }
                )
                continue
            response = client.get_object(Bucket=bucket, Key=key, VersionId=version_id)
            digest = hashlib.sha256()
            file_id = hashlib.sha256(f"{bucket}\0{key}\0{version_id}".encode()).hexdigest()
            relative_path = f"objects/{bucket}/{file_id}.bin"
            target = args.output / relative_path
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            size = 0
            with target.open("wb") as output:
                while chunk := response["Body"].read(1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            target.chmod(0o600)
            if size != int(response["ContentLength"]):
                raise RuntimeError("tamanho exportado divergiu do S3")
            metadata_sha256 = response.get("Metadata", {}).get("sha256")
            if metadata_sha256 and metadata_sha256 != digest.hexdigest():
                raise RuntimeError("checksum de metadata divergiu do conteúdo")
            entries.append(
                {
                    "bucket": bucket,
                    "key": key,
                    "version_id": version_id,
                    "kind": "version",
                    "is_latest": bool(version.get("IsLatest")),
                    "last_modified": version["LastModified"].astimezone(timezone.utc).isoformat(),
                    "size_bytes": size,
                    "sha256": digest.hexdigest(),
                    "metadata_sha256": metadata_sha256,
                    "content_type": response.get("ContentType") or "application/octet-stream",
                    "relative_path": relative_path,
                }
            )
    manifest = {
        "format": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "endpoint_exported": "private-loopback",
        "bucket_count": len(BUCKETS),
        "entry_count": len(entries),
        "version_count": sum(entry["kind"] == "version" for entry in entries),
        "delete_marker_count": sum(entry["kind"] == "delete_marker" for entry in entries),
        "entries": entries,
    }
    manifest_path = args.output / "object-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    manifest_path.chmod(0o600)
    print(json.dumps({key: manifest[key] for key in ("bucket_count", "entry_count", "version_count", "delete_marker_count")}, sort_keys=True))


def list_versions(client, bucket: str):
    key_marker = None
    version_marker = None
    while True:
        request = {"Bucket": bucket}
        if key_marker:
            request["KeyMarker"] = key_marker
        if version_marker:
            request["VersionIdMarker"] = version_marker
        response = client.list_object_versions(**request)
        versions = [{**item, "kind": "version"} for item in response.get("Versions", [])]
        markers = [{**item, "kind": "delete_marker"} for item in response.get("DeleteMarkers", [])]
        yield from sorted(versions + markers, key=lambda item: (item["Key"], item["LastModified"], item["VersionId"]))
        if not response.get("IsTruncated"):
            return
        key_marker = response["NextKeyMarker"]
        version_marker = response.get("NextVersionIdMarker")


if __name__ == "__main__":
    main()
