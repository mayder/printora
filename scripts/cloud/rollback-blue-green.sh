#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"

require_root
current_slot="$(active_slot)"
rollback_slot="$(other_slot "$current_slot")"
rollback_port="$(slot_port "$rollback_slot")"
rollback_link="$PRINTORA_BASE_PATH/slots/$rollback_slot"
[[ -L "$rollback_link" ]] || fail "slot anterior não possui release para rollback"

systemctl restart "printora-cloud@$rollback_slot.service"
if ! wait_until_ready "$rollback_port" 60; then
  systemctl stop "printora-cloud@$rollback_slot.service" || true
  fail "release anterior não ficou ready; tráfego permaneceu no slot $current_slot"
fi

rollback_release="$(readlink -f "$rollback_link")"
activate_replica "$rollback_release"
switch_nginx_to_slot "$rollback_slot"
printf '%s\n' "$rollback_slot" > "$PRINTORA_ACTIVE_SLOT_FILE.tmp"
mv -f "$PRINTORA_ACTIVE_SLOT_FILE.tmp" "$PRINTORA_ACTIVE_SLOT_FILE"
ln -sfn "$rollback_release" "$PRINTORA_BASE_PATH/current.next"
mv -Tf "$PRINTORA_BASE_PATH/current.next" "$PRINTORA_BASE_PATH/current"
restart_durable_workers
restart_intelligence_worker
sleep "${PRINTORA_DRAIN_SECONDS:-30}"
systemctl stop "printora-cloud@$current_slot.service" || true
standby_status="ready"
if ! start_standby "$current_slot"; then standby_status="degraded"; fi
echo "[printora-cloud] active_slot=$rollback_slot replica_slot=replica standby_slot=$current_slot standby_status=$standby_status status=rolled_back data_restored=false"
