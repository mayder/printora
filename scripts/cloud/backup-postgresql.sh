#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
backup_config="$base_path/shared/backup-target.conf"
cluster="${PRINTORA_POSTGRESQL_CLUSTER:-printora}"
port="${PRINTORA_POSTGRESQL_PORT:-5433}"
archive_dir="/var/lib/postgresql/16/$cluster-wal-archive"

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
[[ -s "$backup_config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
[[ "$cluster" == "printora" && "$port" == "5433" ]] || { echo "cluster PostgreSQL inesperado" >&2; exit 1; }
[[ -d "$archive_dir" ]] || { echo "arquivo WAL PostgreSQL ausente" >&2; exit 1; }
command -v pg_basebackup >/dev/null || { echo "pg_basebackup ausente" >&2; exit 1; }
command -v pg_dump >/dev/null || { echo "pg_dump ausente" >&2; exit 1; }
command -v pg_restore >/dev/null || { echo "pg_restore ausente" >&2; exit 1; }
command -v psql >/dev/null || { echo "psql ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }

set -a
source "$backup_config"
set +a

umask 077
work_dir="$(mktemp -d /tmp/printora-postgresql-backup.XXXXXX)"
trap 'rm -rf -- "$work_dir"' EXIT
chown postgres:postgres "$work_dir"
chmod 0700 "$work_dir"
export RESTIC_CACHE_DIR="$work_dir/restic-cache"
install -d -o root -g root -m 0700 "$RESTIC_CACHE_DIR"
install -d -o postgres -g postgres -m 0700 "$work_dir/base"
dump="$work_dir/printora-postgresql.dump"
manifest="$work_dir/manifest.json"
runuser -u postgres -- pg_basebackup \
  --port="$port" \
  --pgdata="$work_dir/base" \
  --checkpoint=spread \
  --wal-method=stream \
  --format=tar \
  --compress=zstd:6
runuser -u postgres -- pg_dump \
  --port="$port" \
  --dbname=printora_cloud \
  --format=custom \
  --compress=zstd:6 \
  --serializable-deferrable \
  --lock-wait-timeout=30s \
  --no-owner \
  --no-acl \
  --file="$dump"
pg_restore --list "$dump" >/dev/null
requested_wal="$(runuser -u postgres -- psql -p "$port" -d printora_cloud -X -Atqc \
  "SELECT pg_walfile_name(pg_switch_wal())")"
for _attempt in $(seq 1 60); do
  [[ -s "$archive_dir/$requested_wal" ]] && break
  sleep 1
done
[[ -s "$archive_dir/$requested_wal" ]] || { echo "WAL solicitado não foi arquivado" >&2; exit 1; }

database_size="$(runuser -u postgres -- psql -p "$port" -d printora_cloud -X -Atqc \
  'SELECT pg_database_size(current_database())')"
last_archived_wal="$requested_wal"
dump_sha256="$(sha256sum "$dump" | awk '{print $1}')"
python3 - "$manifest" "$database_size" "$dump_sha256" "$last_archived_wal" <<'PY'
import json
import sys
from datetime import datetime, timezone

payload = {
    "backend": "postgresql",
    "cluster": "16/printora",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "database": "printora_cloud",
    "database_size_bytes": int(sys.argv[2]),
    "dump_file": "printora-postgresql.dump",
    "dump_sha256": sys.argv[3],
    "last_archived_wal": sys.argv[4],
    "logical_format": "custom",
    "physical_format": "tar+zstd",
}
with open(sys.argv[1], "w", encoding="utf-8") as output:
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY

restic backup "$work_dir/base" "$dump" "$manifest" "$archive_dir" \
  --tag printora-cloud-postgresql --host printora-cloud
echo "backup PostgreSQL externo criptografado concluído; retenção exige execução supervisionada separada"
