#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
backup_config="$base_path/shared/backup-target.conf"
cluster="${PRINTORA_POSTGRESQL_CLUSTER:-printora}"
port="${PRINTORA_POSTGRESQL_PORT:-5433}"
basebackup_max_rate_kib="${PRINTORA_BASEBACKUP_MAX_RATE_KIB:-1024}"
dump_max_bytes_per_second="${PRINTORA_PG_DUMP_MAX_BYTES_PER_SECOND:-262144}"
archive_dir="/var/lib/postgresql/16/$cluster-wal-archive"
state_dir="${PRINTORA_RECOVERY_STATE_DIR:-/var/lib/printora-cloud/recovery}"
state_file="$state_dir/full-backup.json"
started_epoch="$(date +%s)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rate_limiter="$script_dir/rate-limit-stream.py"

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
[[ -s "$backup_config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
[[ "$cluster" == "printora" && "$port" == "5433" ]] || { echo "cluster PostgreSQL inesperado" >&2; exit 1; }
[[ -d "$archive_dir" ]] || { echo "arquivo WAL PostgreSQL ausente" >&2; exit 1; }
command -v pg_basebackup >/dev/null || { echo "pg_basebackup ausente" >&2; exit 1; }
command -v pg_dump >/dev/null || { echo "pg_dump ausente" >&2; exit 1; }
command -v pg_restore >/dev/null || { echo "pg_restore ausente" >&2; exit 1; }
command -v psql >/dev/null || { echo "psql ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
[[ -x /usr/local/libexec/printora-cloud/export-object-storage-backup.py ]] || { echo "exportador de objetos ausente" >&2; exit 1; }
[[ -x "$rate_limiter" ]] || { echo "limitador de stream ausente" >&2; exit 1; }
[[ "$basebackup_max_rate_kib" =~ ^[0-9]+$ ]] \
  && (( basebackup_max_rate_kib >= 1024 && basebackup_max_rate_kib <= 65536 )) \
  || { echo "taxa física de backup inválida" >&2; exit 1; }
[[ "$dump_max_bytes_per_second" =~ ^[0-9]+$ ]] \
  && (( dump_max_bytes_per_second >= 262144 && dump_max_bytes_per_second <= 67108864 )) \
  || { echo "taxa lógica de backup inválida" >&2; exit 1; }

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
configuration_dir="$work_dir/configuration"
install -d -o root -g root -m 0700 "$configuration_dir"
copy_configuration() {
  local source="$1"
  local destination="$2"
  local required="${3:-true}"
  if [[ ! -f "$source" ]]; then
    [[ "$required" == "false" ]] && return 0
    echo "configuração obrigatória ausente: $source" >&2
    exit 1
  fi
  install -o root -g root -m 0600 "$source" "$configuration_dir/$destination"
}
copy_configuration "$base_path/shared/printora-cloud.env" printora-cloud.env
copy_configuration "$base_path/shared/active-slot" active-slot
copy_configuration /etc/printora-cloud/postgresql.env postgresql.env
copy_configuration /etc/printora-cloud/redis.env redis.env
copy_configuration /etc/printora-cloud/object-storage.env object-storage.env
copy_configuration /etc/printora-cloud/workers/outbox.env worker-outbox.env
copy_configuration /etc/printora-cloud/workers/critical.env worker-critical.env
copy_configuration /etc/printora-cloud/workers/default.env worker-default.env
copy_configuration /etc/printora-cloud/workers/bulk.env worker-bulk.env
copy_configuration /etc/nginx/sites-available/print3dmaker.xyz.conf nginx-vhost.conf
copy_configuration "$base_path/shared/nginx/upstream-blue.conf" nginx-upstream-blue.conf
copy_configuration "$base_path/shared/nginx/upstream-green.conf" nginx-upstream-green.conf
set -a
source /etc/printora-object-storage/credentials.env
set +a
"$base_path/current/venv/bin/python" /usr/local/libexec/printora-cloud/export-object-storage-backup.py \
  --output "$work_dir/object-storage"
unset MINIO_ROOT_USER MINIO_ROOT_PASSWORD PRINTORA_OBJECT_STORAGE_ACCESS_KEY PRINTORA_OBJECT_STORAGE_SECRET_KEY
runuser -u postgres -- pg_basebackup \
  --port="$port" \
  --pgdata="$work_dir/base" \
  --checkpoint=spread \
  --max-rate="$basebackup_max_rate_kib" \
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
  --file=- \
  | "$rate_limiter" --bytes-per-second "$dump_max_bytes_per_second" > "$dump"
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
object_manifest_sha256="$(sha256sum "$work_dir/object-storage/object-manifest.json" | awk '{print $1}')"
object_version_count="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version_count"])' "$work_dir/object-storage/object-manifest.json")"
python3 - "$manifest" "$database_size" "$dump_sha256" "$last_archived_wal" "$object_manifest_sha256" "$object_version_count" "$configuration_dir" "${PRINTORA_RECOVERY_CUSTODY_ID:-}" <<'PY'
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

configuration_dir = pathlib.Path(sys.argv[7])
custody_id = sys.argv[8].strip()
if not custody_id:
    raise SystemExit("PRINTORA_RECOVERY_CUSTODY_ID ausente")
configuration_sha256 = {}
for path in sorted(configuration_dir.iterdir()):
    configuration_sha256[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
payload = {
    "backend": "postgresql",
    "cluster": "16/printora",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "database": "printora_cloud",
    "database_size_bytes": int(sys.argv[2]),
    "configuration_file_count": len(configuration_sha256),
    "configuration_sha256": configuration_sha256,
    "recovery_custody_id": custody_id,
    "dump_file": "printora-postgresql.dump",
    "dump_sha256": sys.argv[3],
    "last_archived_wal": sys.argv[4],
    "logical_format": "custom",
    "object_manifest_sha256": sys.argv[5],
    "object_version_count": int(sys.argv[6]),
    "physical_format": "tar+zstd",
}
with open(sys.argv[1], "w", encoding="utf-8") as output:
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY

restic backup "$work_dir/base" "$dump" "$manifest" "$archive_dir" "$work_dir/object-storage" "$configuration_dir" \
  --tag printora-cloud-postgresql --host printora-cloud
install -d -o root -g root -m 0700 "$state_dir"
state_next="$state_file.next"
python3 - "$state_next" "$database_size" "$object_version_count" \
  "$(( $(date +%s) - started_epoch ))" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

payload = {
    "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "database_size_bytes": int(sys.argv[2]),
    "duration_seconds": int(sys.argv[4]),
    "includes": ["configuration", "logical", "objects", "physical", "wal"],
    "object_version_count": int(sys.argv[3]),
    "status": "passed",
}
path = pathlib.Path(sys.argv[1])
path.write_text(json.dumps(payload, sort_keys=True) + "\n")
path.chmod(0o600)
PY
mv -f "$state_next" "$state_file"
echo "backup PostgreSQL externo criptografado concluído; retenção exige execução supervisionada separada"
