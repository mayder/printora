#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
duration_seconds="${PRINTORA_SOAK_SECONDS:-600}"
batch_requests="${PRINTORA_SOAK_BATCH_REQUESTS:-100}"
concurrency="${PRINTORA_SOAK_CONCURRENCY:-20}"
target_rps="${PRINTORA_SOAK_TARGET_RPS:-5}"
url="${PRINTORA_SOAK_URL:-https://print3dmaker.xyz/health}"
load_script="$base_path/current/scripts/cloud/load-smoke.py"
[[ "$duration_seconds" =~ ^[1-9][0-9]*$ ]] || { echo "duração inválida" >&2; exit 64; }
[[ "$batch_requests" =~ ^[1-9][0-9]*$ ]] || { echo "lote inválido" >&2; exit 64; }
[[ "$target_rps" =~ ^[1-9][0-9]*$ ]] || { echo "taxa inválida" >&2; exit 64; }
[[ -x "$load_script" ]] || { echo "script de carga ausente" >&2; exit 66; }

deadline=$((SECONDS + duration_seconds))
batch_interval=$(((batch_requests + target_rps - 1) / target_rps))
batches=0
requests=0
while (( SECONDS < deadline )); do
  batch_started=$SECONDS
  "$load_script" "$url" --requests "$batch_requests" --concurrency "$concurrency" --p95-ms 1500
  batches=$((batches + 1))
  requests=$((requests + batch_requests))
  remaining=$((batch_interval - (SECONDS - batch_started)))
  until_deadline=$((deadline - SECONDS))
  if (( remaining > 0 && until_deadline > 0 )); then
    (( remaining > until_deadline )) && remaining=$until_deadline
    sleep "$remaining"
  fi
done
echo "[printora-cloud] soak_seconds=$duration_seconds target_rps=$target_rps batches=$batches requests=$requests errors=0 status=passed"
