#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
duration_seconds="${PRINTORA_SOAK_SECONDS:-600}"
batch_requests="${PRINTORA_SOAK_BATCH_REQUESTS:-100}"
concurrency="${PRINTORA_SOAK_CONCURRENCY:-20}"
url="${PRINTORA_SOAK_URL:-https://print3dmaker.xyz/health}"
load_script="$base_path/current/scripts/cloud/load-smoke.py"
[[ "$duration_seconds" =~ ^[1-9][0-9]*$ ]] || { echo "duração inválida" >&2; exit 64; }
[[ -x "$load_script" ]] || { echo "script de carga ausente" >&2; exit 66; }

deadline=$((SECONDS + duration_seconds))
batches=0
requests=0
while (( SECONDS < deadline )); do
  "$load_script" "$url" --requests "$batch_requests" --concurrency "$concurrency" --p95-ms 1500
  batches=$((batches + 1))
  requests=$((requests + batch_requests))
done
echo "[printora-cloud] soak_seconds=$duration_seconds batches=$batches requests=$requests errors=0 status=passed"
