#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_PATH="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
DEPLOY_USER="${PRINTORA_DEPLOY_USER:-deploy}"
VHOST=/etc/nginx/sites-available/print3dmaker.xyz.conf
VHOST_BACKUP="$VHOST.before-blue-green"

id "$DEPLOY_USER" >/dev/null
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 0750 \
  "$BASE_PATH/releases" "$BASE_PATH/slots" "$BASE_PATH/shared/data" \
  "$BASE_PATH/shared/logs" "$BASE_PATH/shared/slots" "$BASE_PATH/shared/nginx" \
  "$BASE_PATH/shared/backup-cache"

install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud@.service" /etc/systemd/system/printora-cloud@.service
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud-backup.service" /etc/systemd/system/printora-cloud-backup.service
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud-backup.timer" /etc/systemd/system/printora-cloud-backup.timer
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud-worker@.service" /etc/systemd/system/printora-cloud-worker@.service
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud-workers.target" /etc/systemd/system/printora-cloud-workers.target
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/printora-cloud-intelligence.service" /etc/systemd/system/printora-cloud-intelligence.service
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/redis-printora.service" /etc/systemd/system/redis-printora.service
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/printora-cloud-upstream-blue.conf" "$BASE_PATH/shared/nginx/upstream-blue.conf"
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/printora-cloud-upstream-green.conf" "$BASE_PATH/shared/nginx/upstream-green.conf"
install -o root -g root -m 0644 "$ROOT_DIR/packaging/logrotate/printora-cloud" /etc/logrotate.d/printora-cloud
install -d -o root -g root -m 0755 /usr/local/libexec/printora-cloud
install -d -o root -g deploy -m 0750 /etc/printora-cloud/workers
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/common.sh" /usr/local/libexec/printora-cloud/common.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/backup-postgresql.sh" /usr/local/libexec/printora-cloud/backup-postgresql.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/restore-postgresql-backup-test.sh" /usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/preview-backup-retention.sh" /usr/local/libexec/printora-cloud/preview-backup-retention.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/apply-postgresql-schema.sh" /usr/local/libexec/printora-cloud/apply-postgresql-schema.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/start-worker.sh" /usr/local/libexec/printora-cloud/start-worker.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/run-object-storage-tool.sh" /usr/local/libexec/printora-cloud/run-object-storage-tool.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/validate-object-storage-app.py" /usr/local/libexec/printora-cloud/validate-object-storage.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/migrate-object-storage.py" /usr/local/libexec/printora-cloud/migrate-object-storage.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/reconcile-object-storage.py" /usr/local/libexec/printora-cloud/reconcile-object-storage.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/search-rebuild.py" /usr/local/libexec/printora-cloud/search-rebuild.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/export-object-storage-backup.py" /usr/local/libexec/printora-cloud/export-object-storage-backup.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/probe-search-outbox.py" /usr/local/libexec/printora-cloud/probe-search-outbox.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/probe-search-quality.py" /usr/local/libexec/printora-cloud/probe-search-quality.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/audit-durable-execution.py" /usr/local/libexec/printora-cloud/audit-durable-execution.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/retention-durable-execution.py" /usr/local/libexec/printora-cloud/retention-durable-execution.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/load-durable-execution.py" /usr/local/libexec/printora-cloud/load-durable-execution.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/probe-worker-recovery.py" /usr/local/libexec/printora-cloud/probe-worker-recovery.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/probe-active-active.sh" /usr/local/libexec/printora-cloud/probe-active-active.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/soak-cloud.sh" /usr/local/libexec/printora-cloud/soak-cloud.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/soak-observer.py" /usr/local/libexec/printora-cloud/soak-observer.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/audit-capacity.sh" /usr/local/libexec/printora-cloud/audit-capacity.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/probe-analytics-intelligence.py" /usr/local/libexec/printora-cloud/probe-analytics-intelligence.py
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/audit-final-architecture.sh" /usr/local/libexec/printora-cloud/audit-final-architecture.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/deploy-blue-green.sh" /usr/local/sbin/printora-cloud-deploy
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/rollback-blue-green.sh" /usr/local/sbin/printora-cloud-rollback
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/preflight.sh" /usr/local/sbin/printora-cloud-preflight

printf 'PRINTORA_WORKER_CONCURRENCY=1\n' > /etc/printora-cloud/workers/outbox.env
printf 'PRINTORA_WORKER_CONCURRENCY=2\n' > /etc/printora-cloud/workers/critical.env
printf 'PRINTORA_WORKER_CONCURRENCY=2\n' > /etc/printora-cloud/workers/default.env
printf 'PRINTORA_WORKER_CONCURRENCY=1\n' > /etc/printora-cloud/workers/bulk.env
chown root:deploy /etc/printora-cloud/workers/*.env
chmod 0640 /etc/printora-cloud/workers/*.env

printf 'PRINTORA_PORT=8069\nPRINTORA_SLOT=blue\nPRINTORA_RUNTIME_PROFILE=cloud\n' > "$BASE_PATH/shared/slots/blue.env"
printf 'PRINTORA_PORT=8070\nPRINTORA_SLOT=green\nPRINTORA_RUNTIME_PROFILE=cloud\n' > "$BASE_PATH/shared/slots/green.env"
printf 'PRINTORA_PORT=8071\nPRINTORA_SLOT=replica\nPRINTORA_RUNTIME_PROFILE=cloud\n' > "$BASE_PATH/shared/slots/replica.env"
chown "$DEPLOY_USER:$DEPLOY_USER" "$BASE_PATH/shared/slots/blue.env" "$BASE_PATH/shared/slots/green.env" "$BASE_PATH/shared/slots/replica.env"
chmod 0640 "$BASE_PATH/shared/slots/blue.env" "$BASE_PATH/shared/slots/green.env" "$BASE_PATH/shared/slots/replica.env"

if [[ -s "$VHOST" && ! -e "$VHOST_BACKUP" ]]; then cp -a "$VHOST" "$VHOST_BACKUP"; fi
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/print3dmaker.xyz.conf" "$VHOST"
ln -sfn "$BASE_PATH/shared/nginx/upstream-blue.conf" /etc/nginx/conf.d/printora-cloud-active.conf
printf 'blue\n' > "$BASE_PATH/shared/active-slot"
chown "$DEPLOY_USER:$DEPLOY_USER" "$BASE_PATH/shared/active-slot"

install -o root -g root -m 0440 "$ROOT_DIR/packaging/sudoers/printora-cloud-deploy" /etc/sudoers.d/printora-cloud-deploy
visudo -cf /etc/sudoers.d/printora-cloud-deploy
systemctl daemon-reload
systemctl enable --now printora-cloud-backup.timer
systemctl enable printora-cloud-workers.target
systemctl enable printora-cloud-intelligence.service
nginx -t
systemctl reload nginx
echo "Bootstrap instalado sem interromper a instância legada em 8069."
