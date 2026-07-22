#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
config="$base_path/shared/backup-target.conf"
[[ -s "$config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
command -v pg_config >/dev/null || { echo "pg_config ausente" >&2; exit 1; }

set -a
source "$config"
set +a

restore_root="$(mktemp -d /var/lib/postgresql/printora-restore-test.XXXXXX)"
cluster="$restore_root/cluster"
socket_dir="$restore_root/socket"
restored="$restore_root/restored"
export RESTIC_CACHE_DIR="$restore_root/restic-cache"
started=0
cleanup() {
  if [[ "$started" -eq 1 ]]; then
    runuser -u postgres -- "$pg_bin/pg_ctl" -D "$cluster" -m fast -w stop >/dev/null || true
  fi
  case "$restore_root" in
    /var/lib/postgresql/printora-restore-test.*) rm -rf -- "$restore_root" ;;
    *) echo "diretório temporário inesperado; limpeza recusada" >&2 ;;
  esac
}
trap cleanup EXIT

restic restore latest --tag printora-cloud-postgresql --target "$restored" \
  --include '/tmp/**/base/base.tar.zst' \
  --include '/tmp/**/base/pg_wal.tar*' \
  --include '/tmp/**/manifest.json' \
  --include '/tmp/**/printora-postgresql.dump'
dump="$(find "$restored" -type f -name printora-postgresql.dump -print -quit)"
manifest="$(find "$restored" -type f -name manifest.json -print -quit)"
base_tar="$(find "$restored" -type f -name base.tar.zst -print -quit)"
wal_tar="$(find "$restored" -type f \( -name pg_wal.tar.zst -o -name pg_wal.tar \) -print -quit)"
[[ -n "$dump" && -n "$manifest" && -n "$base_tar" && -n "$wal_tar" ]] || {
  echo "backup restaurado incompleto" >&2
  exit 1
}
expected_sha256="$(python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    print(json.load(source)["dump_sha256"])
PY
)"
last_archived_wal="$(python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    print(json.load(source)["last_archived_wal"])
PY
)"
[[ "$last_archived_wal" =~ ^[0-9A-F]{24}$ ]] || { echo "WAL final inválido" >&2; exit 1; }
restic restore latest --tag printora-cloud-postgresql --target "$restored" \
  --include "/var/lib/postgresql/16/printora-wal-archive/$last_archived_wal"
archive_dir="$(find "$restored" -type d -name printora-wal-archive -print -quit)"
[[ -s "$archive_dir/$last_archived_wal" ]] || { echo "WAL final ausente" >&2; exit 1; }
"$(pg_config --bindir)/pg_waldump" -n 1 "$archive_dir/$last_archived_wal" >/dev/null
actual_sha256="$(sha256sum "$dump" | awk '{print $1}')"
[[ "$actual_sha256" == "$expected_sha256" ]] || { echo "checksum do dump divergente" >&2; exit 1; }

pg_bin="$(pg_config --bindir)"
chown postgres:postgres "$restore_root"
chmod 0700 "$restore_root"
install -d -o postgres -g postgres -m 0700 "$cluster" "$socket_dir"
chown -R postgres:postgres "$restored"
runuser -u postgres -- tar --zstd -xf "$base_tar" -C "$cluster"
install -d -o postgres -g postgres -m 0700 "$cluster/pg_wal"
case "$wal_tar" in
  *.zst) runuser -u postgres -- tar --zstd -xf "$wal_tar" -C "$cluster/pg_wal" ;;
  *.tar) runuser -u postgres -- tar -xf "$wal_tar" -C "$cluster/pg_wal" ;;
  *) echo "formato do arquivo pg_wal inesperado" >&2; exit 1 ;;
esac
cat > "$cluster/postgresql.conf" <<EOF
listen_addresses = ''
port = 5432
unix_socket_directories = '$socket_dir'
archive_mode = off
fsync = off
full_page_writes = off
synchronous_commit = off
restore_command = 'cp $archive_dir/%f %p'
recovery_target_action = 'promote'
EOF
cat > "$cluster/pg_hba.conf" <<'EOF'
local all all trust
EOF
touch "$cluster/recovery.signal"
chown -R postgres:postgres "$cluster"
started=1
runuser -u postgres -- "$pg_bin/pg_ctl" -D "$cluster" -t 300 -w start >/dev/null
export PGHOST="$socket_dir" PGPORT=5432 PGUSER=postgres PGDATABASE=postgres
for _attempt in $(seq 1 60); do
  if [[ "$(runuser -u postgres -- "$pg_bin/psql" -X -Atqc 'SELECT pg_is_in_recovery()')" == "f" ]]; then
    break
  fi
  sleep 1
done
[[ "$(runuser -u postgres -- "$pg_bin/psql" -X -Atqc 'SELECT pg_is_in_recovery()')" == "f" ]] || {
  echo "restore físico não promoveu dentro do limite" >&2
  exit 1
}
export PGDATABASE=printora_cloud

runuser -u postgres -- "$pg_bin/psql" -X -v ON_ERROR_STOP=1 -At <<'SQL'
DO $$
DECLARE
    application_tables integer;
    schema_revisions integer;
    invalid_foreign_keys integer;
BEGIN
    SELECT COUNT(*) INTO application_tables
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    SELECT COUNT(*) INTO schema_revisions FROM schema_versions;
    SELECT COUNT(*) INTO invalid_foreign_keys
    FROM pg_constraint
    WHERE contype = 'f' AND NOT convalidated;
    IF application_tables = 0 OR schema_revisions = 0 OR invalid_foreign_keys <> 0 THEN
        RAISE EXCEPTION 'restore inválido: tables=%, revisions=%, invalid_fks=%',
            application_tables, schema_revisions, invalid_foreign_keys;
    END IF;
END
$$;
SELECT json_build_object(
    'database', current_database(),
    'in_recovery', pg_is_in_recovery(),
    'tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
    'schema_versions', (SELECT COUNT(*) FROM schema_versions),
    'invalid_foreign_keys', (SELECT COUNT(*) FROM pg_constraint WHERE contype = 'f' AND NOT convalidated)
);
SQL
echo "restore físico PostgreSQL com WAL validado em cluster isolado; aplicação não foi iniciada"
