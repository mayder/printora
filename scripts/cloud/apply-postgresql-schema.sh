#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
release_dir="${1:-}"
base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
release_dir="$(readlink -f "$release_dir")"
case "$release_dir" in
  "$base_path"/releases/*) ;;
  *) echo "ERRO: release fora do diretório imutável" >&2; exit 1 ;;
esac
[[ -s "$release_dir/RELEASE_SHA" ]] || { echo "ERRO: marcador da release ausente" >&2; exit 1; }
[[ -s "$release_dir/backend/sql/postgresql/001_baseline.sql" ]] || {
  echo "ERRO: baseline PostgreSQL ausente" >&2
  exit 1
}
permissions_sql="$release_dir/scripts/cloud/postgresql-runtime-permissions.sql"
[[ -s "$permissions_sql" ]] || { echo "ERRO: grants runtime ausentes" >&2; exit 1; }

{
  printf '%s\n' '\set ON_ERROR_STOP on' 'BEGIN;' \
    "SELECT pg_advisory_xact_lock(hashtextextended('printora:schema', 0));"
  for schema_file in "$release_dir"/backend/sql/postgresql/[0-9]*.sql; do
    [[ "$(basename "$schema_file")" == "001_baseline.sql" ]] && continue
    cat "$schema_file"
  done
  cat "$permissions_sql"
  printf '%s\n' 'COMMIT;'
} | sudo -u postgres psql -p 5433 -d printora_cloud -v ON_ERROR_STOP=1 >/dev/null

echo "Schema PostgreSQL aditivo aplicado pela etapa privilegiada."
