#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
from pathlib import Path

required = {
    "backend/app/object_storage.py": [
        'if runtime_profile == "cloud":',
        'raise RuntimeError("perfil cloud exige PRINTORA_OBJECT_STORAGE_MODE=s3")',
    ],
    "backend/app/search_discovery.py": [
        'search_table = "search_documents" if postgresql else "social_search_index"',
        "idx.search_vector @@ websearch_to_tsquery('simple', ?)",
        'if uses_postgresql():\n                return self._indexed_count(connection)',
    ],
    "packaging/systemd/printora-cloud@.service": [
        "EnvironmentFile=/etc/printora-cloud/object-storage.env",
        "minio-printora.service",
    ],
    "packaging/systemd/printora-cloud-worker@.service": [
        "EnvironmentFile=/etc/printora-cloud/object-storage.env",
        "minio-printora.service",
    ],
}
for file_name, fragments in required.items():
    content = Path(file_name).read_text()
    missing = [fragment for fragment in fragments if fragment not in content]
    if missing:
        raise SystemExit(f"contrato cloud storage/search ausente em {file_name}: {missing}")

for file_name in (
    "backend/app/routes/social_catalog.py",
    "backend/app/routes/print_projects.py",
):
    if "await request.body()" in Path(file_name).read_text():
        raise SystemExit(f"upload cloud voltou a materializar request sem limite em {file_name}")
PY

echo "storage S3-only e busca PostgreSQL-only no perfil cloud validados"
