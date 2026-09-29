#!/usr/bin/env bash
set -euo pipefail

queue_name="${1:-}"
case "$queue_name" in
  outbox|critical|default|bulk) ;;
  *) echo "[printora-worker] fila inválida" >&2; exit 64 ;;
esac

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
active_slot="$(tr -d '[:space:]' < "$base_path/shared/active-slot")"
case "$active_slot" in blue|green) ;; *) echo "[printora-worker] slot ativo inválido" >&2; exit 65 ;; esac

release_dir="$(readlink -f "$base_path/slots/$active_slot")"
[[ -x "$release_dir/venv/bin/python" && -f "$release_dir/backend/app/worker.py" ]] || {
  echo "[printora-worker] release ativa não possui worker compatível" >&2
  exit 66
}

export PRINTORA_RELEASE_SHA="$(basename "$release_dir")"
cd "$release_dir/backend"
exec "$release_dir/venv/bin/python" -m app.worker \
  --queue "$queue_name" \
  --concurrency "${PRINTORA_WORKER_CONCURRENCY:-1}" \
  --poll-seconds "${PRINTORA_WORKER_POLL_SECONDS:-0.5}" \
  --lease-seconds "${PRINTORA_WORKER_LEASE_SECONDS:-45}"
