#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
backup_config="$base_path/shared/backup-target.conf"
database_config="${PRINTORA_POSTGRESQL_ENV:-/etc/printora-cloud/postgresql.env}"
expected_database="${PRINTORA_EXPECTED_DATABASE:-printora_cloud}"

[[ -s "$backup_config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
[[ -s "$database_config" ]] || { echo "configuração PostgreSQL ausente" >&2; exit 1; }
command -v pg_dump >/dev/null || { echo "pg_dump ausente" >&2; exit 1; }
command -v pg_restore >/dev/null || { echo "pg_restore ausente" >&2; exit 1; }
command -v psql >/dev/null || { echo "psql ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }

set -a
source "$backup_config"
source "$database_config"
set +a
[[ -n "${PRINTORA_DATABASE_URL:-}" ]] || { echo "PRINTORA_DATABASE_URL ausente" >&2; exit 1; }

umask 077
work_dir="$(mktemp -d /tmp/printora-postgresql-backup.XXXXXX)"
trap 'rm -rf -- "$work_dir"' EXIT
service_file="$work_dir/pg_service.conf"
printf '[printora_backup]\ndbname=%s\n' "$PRINTORA_DATABASE_URL" > "$service_file"
export PGSERVICEFILE="$service_file" PGSERVICE=printora_backup
unset PRINTORA_DATABASE_URL

actual_database="$(psql -X -Atqc 'SELECT current_database()')"
[[ "$actual_database" == "$expected_database" ]] || {
  echo "banco PostgreSQL inesperado: $actual_database" >&2
  exit 1
}

dump="$work_dir/printora-postgresql.dump"
manifest="$work_dir/manifest.json"
pg_dump \
  --format=custom \
  --compress=zstd:6 \
  --serializable-deferrable \
  --lock-wait-timeout=30s \
  --no-owner \
  --no-acl \
  --file="$dump"
pg_restore --list "$dump" >/dev/null

database_size="$(psql -X -Atqc 'SELECT pg_database_size(current_database())')"
dump_sha256="$(sha256sum "$dump" | awk '{print $1}')"
python3 - "$manifest" "$actual_database" "$database_size" "$dump_sha256" <<'PY'
import json
import sys
from datetime import datetime, timezone

payload = {
    "backend": "postgresql",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "database": sys.argv[2],
    "database_size_bytes": int(sys.argv[3]),
    "dump_file": "printora-postgresql.dump",
    "dump_sha256": sys.argv[4],
    "format": "custom",
}
with open(sys.argv[1], "w", encoding="utf-8") as output:
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY

restic backup "$dump" "$manifest" --tag printora-cloud-postgresql --host printora-cloud
echo "backup PostgreSQL externo criptografado concluído; retenção exige execução supervisionada separada"
