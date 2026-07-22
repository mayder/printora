#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="${PRINTORA_POSTGRESQL_VERSION:-16}"
cluster="${PRINTORA_POSTGRESQL_CLUSTER:-printora}"
port="${PRINTORA_POSTGRESQL_PORT:-5433}"
password_file="${PRINTORA_POSTGRESQL_PASSWORD_FILE:-/etc/printora-cloud/postgresql-password}"
archive_dir="/var/lib/postgresql/$version/$cluster-wal-archive"
config_dir="/etc/postgresql/$version/$cluster"
environment_file="/etc/printora-cloud/postgresql.env"
created=0

[[ "$version" == "16" && "$cluster" == "printora" && "$port" == "5433" ]] || {
  echo "topologia PostgreSQL fora do contrato aprovado" >&2
  exit 1
}
[[ -s "$password_file" ]] || { echo "arquivo de senha PostgreSQL ausente" >&2; exit 1; }
app_password="$(tr -d '\r\n' < "$password_file")"
[[ "$app_password" =~ ^[A-Za-z0-9._~-]{32,}$ ]] || {
  echo "senha PostgreSQL não atende ao formato operacional seguro" >&2
  exit 1
}

if ! pg_lsclusters --no-header | awk -v version="$version" -v cluster="$cluster" \
  '$1 == version && $2 == cluster { found = 1 } END { exit !found }'; then
  pg_createcluster "$version" "$cluster" --port "$port" --start-conf=auto -- \
    --auth-local=peer --auth-host=scram-sha-256 --data-checksums
  created=1
fi

install -d -o postgres -g postgres -m 0700 "$archive_dir"
install -d -o root -g postgres -m 0750 "$config_dir/conf.d"
install -o root -g postgres -m 0640 \
  "$ROOT_DIR/packaging/postgresql/printora.conf" \
  "$config_dir/conf.d/printora.conf"
install -d -o root -g root -m 0755 "/etc/systemd/system/postgresql@$version-$cluster.service.d"
install -o root -g root -m 0644 \
  "$ROOT_DIR/packaging/systemd/postgresql-printora-limits.conf" \
  "/etc/systemd/system/postgresql@$version-$cluster.service.d/limits.conf"
systemctl daemon-reload

if [[ "$created" -eq 1 ]]; then
  pg_ctlcluster "$version" "$cluster" start
elif ! pg_ctlcluster "$version" "$cluster" status >/dev/null 2>&1; then
  pg_ctlcluster "$version" "$cluster" start
else
  configured_archive_mode="$(sudo -u postgres psql -p "$port" -Atqc 'SHOW archive_mode')"
  [[ "$configured_archive_mode" == "on" ]] || {
    echo "cluster existente exige janela explícita para ativar archive_mode" >&2
    exit 1
  }
  pg_ctlcluster "$version" "$cluster" reload
fi

{
  printf "\\set app_password '%s'\n" "$app_password"
  cat "$ROOT_DIR/backend/sql/postgresql/admin/000_cluster_bootstrap.sql"
} | sudo -u postgres psql -p "$port" -v ON_ERROR_STOP=1 >/dev/null

schema_exists="$(sudo -u postgres psql -p "$port" -d printora_cloud -Atqc \
  "SELECT to_regclass('public.schema_versions') IS NOT NULL")"
if [[ "$schema_exists" != "t" ]]; then
  sudo -u postgres psql -p "$port" -d printora_cloud -v ON_ERROR_STOP=1 \
    -f "$ROOT_DIR/backend/sql/postgresql/001_baseline.sql" >/dev/null
  sudo -u postgres psql -p "$port" -d printora_cloud -v ON_ERROR_STOP=1 \
    -f "$ROOT_DIR/backend/sql/postgresql/002_transition_replication_state.sql" >/dev/null
fi
sudo -u postgres psql -p "$port" -d printora_cloud -v ON_ERROR_STOP=1 \
  -f "$ROOT_DIR/scripts/cloud/postgresql-runtime-permissions.sql" >/dev/null

install -d -o root -g deploy -m 0750 /etc/printora-cloud
umask 0027
printf "PRINTORA_DATABASE_URL='postgresql://printora_app:%s@127.0.0.1:%s/printora_cloud'\n" \
  "$app_password" "$port" > "$environment_file"
chown root:deploy "$environment_file"
chmod 0640 "$environment_file"

sudo -u postgres psql -p "$port" -d printora_cloud -v ON_ERROR_STOP=1 -Atqc \
  "SELECT current_database(), current_setting('data_checksums'), current_setting('archive_mode')"
echo "PostgreSQL dedicado do Printora pronto em loopback; nenhuma outra instância foi reiniciada."
