#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
duration_seconds="${PRINTORA_SOAK_SECONDS:-600}"
batch_requests="${PRINTORA_SOAK_BATCH_REQUESTS:-100}"
concurrency="${PRINTORA_SOAK_CONCURRENCY:-20}"
target_rps="${PRINTORA_SOAK_TARGET_RPS:-5}"
observe="${PRINTORA_SOAK_OBSERVE:-0}"
observe_every_seconds="${PRINTORA_SOAK_OBSERVE_EVERY_SECONDS:-60}"
agent_stable_id="${PRINTORA_SOAK_AGENT_STABLE_ID:-}"
expected_agent_version="${PRINTORA_SOAK_EXPECTED_AGENT_VERSION:-}"
url="${PRINTORA_SOAK_URL:-https://print3dmaker.xyz/health}"
load_script="$base_path/current/scripts/cloud/load-smoke.py"
observer_script="$base_path/current/scripts/cloud/soak-observer.py"
runtime_python="$base_path/current/venv/bin/python"
evidence_file="${PRINTORA_SOAK_EVIDENCE_FILE:-$base_path/shared/logs/soak-$(date -u +%Y%m%dT%H%M%SZ).jsonl}"
[[ "$duration_seconds" =~ ^[1-9][0-9]*$ ]] || { echo "duração inválida" >&2; exit 64; }
[[ "$batch_requests" =~ ^[1-9][0-9]*$ ]] || { echo "lote inválido" >&2; exit 64; }
[[ "$target_rps" =~ ^[1-9][0-9]*$ ]] || { echo "taxa inválida" >&2; exit 64; }
[[ -x "$load_script" ]] || { echo "script de carga ausente" >&2; exit 66; }
[[ "$observe" == "0" || "$observe" == "1" ]] || { echo "observação inválida" >&2; exit 64; }
[[ "$observe_every_seconds" =~ ^[1-9][0-9]*$ ]] || { echo "intervalo de observação inválido" >&2; exit 64; }
if [[ "$observe" == "1" ]]; then
  [[ -n "$agent_stable_id" ]] || { echo "agente de soak ausente" >&2; exit 64; }
  [[ -n "$expected_agent_version" ]] || { echo "versão esperada do agente ausente" >&2; exit 64; }
  [[ -x "$observer_script" && -x "$runtime_python" ]] || { echo "observador de soak ausente" >&2; exit 66; }
  [[ "$evidence_file" == "$base_path/shared/logs/"* ]] || { echo "evidência fora do diretório permitido" >&2; exit 64; }
  install -d -o deploy -g deploy -m 0750 "$(dirname "$evidence_file")"
  touch "$evidence_file"
  chown deploy:deploy "$evidence_file"
  chmod 0640 "$evidence_file"
fi

deadline=$((SECONDS + duration_seconds))
batch_interval=$(((batch_requests + target_rps - 1) / target_rps))
next_observation=$SECONDS
batches=0
requests=0
while (( SECONDS < deadline )); do
  batch_started=$SECONDS
  if ! load_report="$("$load_script" "$url" --requests "$batch_requests" --concurrency "$concurrency" --p95-ms 1500 --p99-ms 2500)"; then
    echo "$load_report"
    if [[ "$observe" == "1" ]]; then printf '%s\n' "$load_report" >> "$evidence_file"; fi
    exit 1
  fi
  echo "$load_report"
  if [[ "$observe" == "1" ]]; then
    printf '%s\n' "$load_report" >> "$evidence_file"
    if (( SECONDS >= next_observation )); then
      if ! observation="$("$runtime_python" "$observer_script" \
        --agent-stable-id "$agent_stable_id" \
        --expected-agent-version "$expected_agent_version" \
        --evidence-file "$evidence_file" \
        --base-path "$base_path")"; then
        echo "$observation"
        printf '%s\n' "$observation" >> "$evidence_file"
        exit 1
      fi
      echo "$observation"
      printf '%s\n' "$observation" >> "$evidence_file"
      next_observation=$((SECONDS + observe_every_seconds))
    fi
  fi
  batches=$((batches + 1))
  requests=$((requests + batch_requests))
  remaining=$((batch_interval - (SECONDS - batch_started)))
  until_deadline=$((deadline - SECONDS))
  if (( remaining > 0 && until_deadline > 0 )); then
    (( remaining > until_deadline )) && remaining=$until_deadline
    sleep "$remaining"
  fi
done
echo "[printora-cloud] soak_seconds=$duration_seconds target_rps=$target_rps batches=$batches requests=$requests errors=0 observed=$observe evidence=$(basename "$evidence_file") status=passed"
