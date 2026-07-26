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
running_script_sha="$(sha256sum "$0" | awk '{print $1}')"

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
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-intelligence.service" /etc/systemd/system/printora-cloud-intelligence.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-backup.service" /etc/systemd/system/printora-cloud-backup.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-backup.timer" /etc/systemd/system/printora-cloud-backup.timer
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-wal-sync.service" /etc/systemd/system/printora-cloud-wal-sync.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-wal-sync.timer" /etc/systemd/system/printora-cloud-wal-sync.timer
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-recovery-monitor.service" /etc/systemd/system/printora-cloud-recovery-monitor.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-recovery-monitor.timer" /etc/systemd/system/printora-cloud-recovery-monitor.timer
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-restore-test.service" /etc/systemd/system/printora-cloud-restore-test.service
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-restore-test.timer" /etc/systemd/system/printora-cloud-restore-test.timer
install -o root -g root -m 0644 "$release_dir/packaging/systemd/printora-cloud-recovery-alert@.service" /etc/systemd/system/printora-cloud-recovery-alert@.service
install -o root -g root -m 0644 "$release_dir/packaging/logrotate/printora-cloud" /etc/logrotate.d/printora-cloud
install -d -o root -g root -m 0755 /etc/systemd/journald.conf.d
if ! cmp -s \
  "$release_dir/packaging/systemd/journald-printora-cloud.conf" \
  /etc/systemd/journald.conf.d/printora-cloud.conf; then
  install -o root -g root -m 0644 \
    "$release_dir/packaging/systemd/journald-printora-cloud.conf" \
    /etc/systemd/journald.conf.d/printora-cloud.conf
  systemctl restart systemd-journald
fi
install -o root -g root -m 0644 "$release_dir/packaging/nginx/printora-cloud-upstream-blue.conf" "$PRINTORA_BASE_PATH/shared/nginx/upstream-blue.conf"
install -o root -g root -m 0644 "$release_dir/packaging/nginx/printora-cloud-upstream-green.conf" "$PRINTORA_BASE_PATH/shared/nginx/upstream-green.conf"
install -o root -g root -m 0755 "$release_dir/scripts/cloud/common.sh" /usr/local/libexec/printora-cloud/common.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/apply-postgresql-schema.sh" /usr/local/libexec/printora-cloud/apply-postgresql-schema.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/start-worker.sh" /usr/local/libexec/printora-cloud/start-worker.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/backup-postgresql.sh" /usr/local/libexec/printora-cloud/backup-postgresql.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/restore-postgresql-backup-test.sh" /usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/sync-postgresql-wal.sh" /usr/local/libexec/printora-cloud/sync-postgresql-wal.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/recovery-readiness.py" /usr/local/libexec/printora-cloud/recovery-readiness.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/run-restore-test.sh" /usr/local/libexec/printora-cloud/run-restore-test.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/emit-recovery-alert.sh" /usr/local/libexec/printora-cloud/emit-recovery-alert.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/preview-backup-retention.sh" /usr/local/libexec/printora-cloud/preview-backup-retention.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/run-object-storage-tool.sh" /usr/local/libexec/printora-cloud/run-object-storage-tool.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/validate-object-storage-app.py" /usr/local/libexec/printora-cloud/validate-object-storage.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/migrate-object-storage.py" /usr/local/libexec/printora-cloud/migrate-object-storage.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/reconcile-object-storage.py" /usr/local/libexec/printora-cloud/reconcile-object-storage.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/search-rebuild.py" /usr/local/libexec/printora-cloud/search-rebuild.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/export-object-storage-backup.py" /usr/local/libexec/printora-cloud/export-object-storage-backup.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/probe-search-outbox.py" /usr/local/libexec/printora-cloud/probe-search-outbox.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/probe-search-quality.py" /usr/local/libexec/printora-cloud/probe-search-quality.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/probe-active-active.sh" /usr/local/libexec/printora-cloud/probe-active-active.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/soak-cloud.sh" /usr/local/libexec/printora-cloud/soak-cloud.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/soak-observer.py" /usr/local/libexec/printora-cloud/soak-observer.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/summarize-soak.py" /usr/local/libexec/printora-cloud/summarize-soak.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/audit-capacity.sh" /usr/local/libexec/printora-cloud/audit-capacity.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/probe-analytics-intelligence.py" /usr/local/libexec/printora-cloud/probe-analytics-intelligence.py
install -o root -g root -m 0755 "$release_dir/scripts/cloud/audit-final-architecture.sh" /usr/local/libexec/printora-cloud/audit-final-architecture.sh
install -o root -g root -m 0755 "$release_dir/scripts/cloud/preflight.sh" /usr/local/sbin/printora-cloud-preflight
install -o root -g root -m 0755 "$release_dir/scripts/cloud/deploy-blue-green.sh" /usr/local/sbin/printora-cloud-deploy
install -o root -g root -m 0755 "$release_dir/scripts/cloud/retain-releases.sh" /usr/local/sbin/printora-cloud-retain-releases
installed_script_sha="$(sha256sum /usr/local/sbin/printora-cloud-deploy | awk '{print $1}')"
if [[ "${PRINTORA_DEPLOY_REEXECUTED:-0}" != "1" && "$running_script_sha" != "$installed_script_sha" ]]; then
  echo "[printora-cloud] deploy_entrypoint=updated action=reexec"
  exec env PRINTORA_DEPLOY_REEXECUTED=1 /usr/local/sbin/printora-cloud-deploy "$release_sha"
fi
systemctl daemon-reload
install -d -o root -g postgres -m 0750 /etc/postgresql/16/printora/conf.d
install -o root -g postgres -m 0640 \
  "$release_dir/packaging/postgresql/printora.conf" \
  /etc/postgresql/16/printora/conf.d/printora.conf
pg_ctlcluster 16 printora reload
archive_timeout="$(
  runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc \
    "SELECT extract(epoch FROM current_setting('archive_timeout')::interval)::int"
)"
[[ "$archive_timeout" == "120" ]] || fail "archive_timeout não aplicado"
systemctl enable --now printora-cloud-backup.timer
systemctl enable --now printora-cloud-wal-sync.timer
systemctl enable --now printora-cloud-restore-test.timer
systemctl enable --now printora-cloud-recovery-monitor.timer

replica_env="$PRINTORA_BASE_PATH/shared/slots/replica.env"
if [[ ! -s "$replica_env" ]]; then
  printf 'PRINTORA_PORT=8071\nPRINTORA_SLOT=replica\nPRINTORA_RUNTIME_PROFILE=cloud\n' > "$replica_env.next"
  chown deploy:deploy "$replica_env.next"
  chmod 0640 "$replica_env.next"
  mv -Tf "$replica_env.next" "$replica_env"
fi

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
activate_replica "$release_dir"
switch_nginx_to_slot "$candidate_slot"
printf '%s\n' "$candidate_slot" > "$PRINTORA_ACTIVE_SLOT_FILE.tmp"
mv -f "$PRINTORA_ACTIVE_SLOT_FILE.tmp" "$PRINTORA_ACTIVE_SLOT_FILE"
ln -sfn "$release_dir" "$PRINTORA_BASE_PATH/current.next"
mv -Tf "$PRINTORA_BASE_PATH/current.next" "$PRINTORA_BASE_PATH/current"
restart_durable_workers
restart_intelligence_worker

drain_seconds="${PRINTORA_DRAIN_SECONDS:-30}"
sleep "$drain_seconds"
systemctl stop "printora-cloud@$current_slot.service" || true
standby_status="ready"
if ! start_standby "$current_slot"; then standby_status="degraded"; fi
retention_status="ok"
if ! /usr/local/sbin/printora-cloud-retain-releases --apply; then
  retention_status="failed"
  echo "[printora-cloud] ALERTA: retenção de releases falhou; links ativos foram preservados" >&2
fi
echo "[printora-cloud] release=$release_sha active_slot=$candidate_slot replica_slot=replica standby_slot=$current_slot standby_status=$standby_status retention_status=$retention_status status=deployed"
