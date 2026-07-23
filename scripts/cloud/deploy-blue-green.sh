#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"

require_root
release_sha="${1:-}"
[[ "$release_sha" =~ ^[0-9a-f]{7,64}$ ]] || fail "SHA de release inválido"

release_dir="$PRINTORA_BASE_PATH/releases/$release_sha"
[[ -d "$release_dir/backend" ]] || fail "backend da release ausente"
[[ -x "$release_dir/venv/bin/python" ]] || fail "venv imutável da release ausente"
[[ -s "$release_dir/frontend/dist/index.html" ]] || fail "frontend da release ausente"

# Runtime contracts are versioned with the immutable release. Updating them
# before the candidate starts prevents code/env drift while the active slot
# continues serving with its already loaded unit definition.
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud@.service" /etc/systemd/system/printora-cloud@.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-worker@.service" /etc/systemd/system/printora-cloud-worker@.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-workers.target" /etc/systemd/system/printora-cloud-workers.target
install -o root -g root -m 0755 "$release_dir/scripts/cloud/common.sh" /usr/local/libexec/printora-cloud/common.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/apply-postgresql-schema.sh" /usr/local/libexec/printora-cloud/apply-postgresql-schema.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/start-worker.sh" /usr/local/libexec/printora-cloud/start-worker.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/preflight.sh" /usr/local/sbin/printora-cloud-preflight
install -o root -g root -m 0755 "$release_dir/scripts/cloud/deploy-blue-green.sh" /usr/local/sbin/printora-cloud-deploy
systemctl daemon-reload

"$SCRIPT_DIR/apply-postgresql-schema.sh" "$release_dir"

current_slot="$(active_slot)"
candidate_slot="$(other_slot "$current_slot")"
candidate_port="$(slot_port "$candidate_slot")"
candidate_link="$PRINTORA_BASE_PATH/slots/$candidate_slot"

ln -sfn "$release_dir" "$candidate_link.next"
mv -Tf "$candidate_link.next" "$candidate_link"
systemctl restart "printora-cloud@$candidate_slot.service"

if ! wait_until_ready "$candidate_port" 60; then
  systemctl status "printora-cloud@$candidate_slot.service" --no-pager || true
  journalctl -u "printora-cloud@$candidate_slot.service" -n 120 --no-pager || true
  systemctl stop "printora-cloud@$candidate_slot.service" || true
  fail "candidato não ficou ready; tráfego permaneceu no slot $current_slot"
fi

curl --max-time 5 -fsS "http://127.0.0.1:$candidate_port/health" >/dev/null
curl --max-time 5 -fsS "http://127.0.0.1:$candidate_port/api/catalog" >/dev/null
switch_nginx_to_slot "$candidate_slot"
printf '%s\n' "$candidate_slot" > "$PRINTORA_ACTIVE_SLOT_FILE.tmp"
mv -f "$PRINTORA_ACTIVE_SLOT_FILE.tmp" "$PRINTORA_ACTIVE_SLOT_FILE"
ln -sfn "$release_dir" "$PRINTORA_BASE_PATH/current.next"
mv -Tf "$PRINTORA_BASE_PATH/current.next" "$PRINTORA_BASE_PATH/current"
restart_durable_workers

drain_seconds="${PRINTORA_DRAIN_SECONDS:-30}"
sleep "$drain_seconds"
systemctl stop "printora-cloud@$current_slot.service" || true
standby_status="ready"
if ! start_standby "$current_slot"; then standby_status="degraded"; fi
echo "[printora-cloud] release=$release_sha active_slot=$candidate_slot standby_slot=$current_slot standby_status=$standby_status status=deployed"
