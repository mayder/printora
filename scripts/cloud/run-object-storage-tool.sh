#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
tool="${1:-}"
shift || true
case "$tool" in
  validate|migrate|reconcile) ;;
  *) echo "ERRO: ferramenta deve ser validate, migrate ou reconcile" >&2; exit 2 ;;
esac

active_slot="$(cat "$base_path/shared/active-slot")"
case "$active_slot" in blue|green) ;; *) echo "ERRO: slot ativo inválido" >&2; exit 1 ;; esac

set -a
source "$base_path/shared/printora-cloud.env"
source /etc/printora-cloud/postgresql.env
source /etc/printora-cloud/redis.env
source /etc/printora-cloud/object-storage.env
source "$base_path/shared/slots/$active_slot.env"
set +a

cd "$base_path/current/backend"
export PYTHONPATH="$PWD"
exec "$base_path/current/venv/bin/python" "/usr/local/libexec/printora-cloud/${tool}-object-storage.py" "$@"
