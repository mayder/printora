#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"

require_root
active="$(active_slot)"
active_port="$(slot_port "$active")"
replica_port="$(slot_port replica)"
load_script="$PRINTORA_BASE_PATH/current/scripts/cloud/load-smoke.py"
runtime_python="$PRINTORA_BASE_PATH/current/venv/bin/python"
chaos_url="${PRINTORA_CHAOS_URL:-https://print3dmaker.xyz/health}"
[[ -x "$load_script" ]] || fail "script de carga ausente"
[[ -x "$runtime_python" ]] || fail "runtime Python da release ausente"
wait_until_ready "$active_port" 5 || fail "instância ativa não está ready"
wait_until_ready "$replica_port" 5 || fail "réplica não está ready"
nginx -T 2>&1 | grep "127.0.0.1:$replica_port" >/dev/null || fail "réplica ausente do upstream carregado"

restore_active() {
  systemctl start "printora-cloud@$active.service" || true
  wait_until_ready "$active_port" 60 || true
}
trap restore_active EXIT

systemctl stop "printora-cloud@$active.service"
"$runtime_python" "$load_script" "$chaos_url" \
  --requests 300 \
  --concurrency 20 \
  --connection-mode pooled \
  --p95-ms 2000
wait_until_ready "$replica_port" 5 || fail "réplica falhou durante o caos"
restore_active
trap - EXIT
wait_until_ready "$active_port" 5 || fail "instância ativa não recuperou"
echo "[printora-cloud] chaos=active_instance_stopped requests=300 errors=0 recovery=passed"
