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
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/printora-cloud-upstream-blue.conf" "$BASE_PATH/shared/nginx/upstream-blue.conf"
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/printora-cloud-upstream-green.conf" "$BASE_PATH/shared/nginx/upstream-green.conf"
install -o root -g root -m 0644 "$ROOT_DIR/packaging/logrotate/printora-cloud" /etc/logrotate.d/printora-cloud
install -d -o root -g root -m 0755 /usr/local/libexec/printora-cloud
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/common.sh" /usr/local/libexec/printora-cloud/common.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/backup-sqlite.sh" /usr/local/libexec/printora-cloud/backup-sqlite.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/restore-backup-test.sh" /usr/local/libexec/printora-cloud/restore-backup-test.sh
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/deploy-blue-green.sh" /usr/local/sbin/printora-cloud-deploy
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/rollback-blue-green.sh" /usr/local/sbin/printora-cloud-rollback
install -o root -g root -m 0755 "$ROOT_DIR/scripts/cloud/preflight.sh" /usr/local/sbin/printora-cloud-preflight

printf 'PRINTORA_PORT=8069\nPRINTORA_SLOT=blue\n' > "$BASE_PATH/shared/slots/blue.env"
printf 'PRINTORA_PORT=8070\nPRINTORA_SLOT=green\n' > "$BASE_PATH/shared/slots/green.env"
chown "$DEPLOY_USER:$DEPLOY_USER" "$BASE_PATH/shared/slots/blue.env" "$BASE_PATH/shared/slots/green.env"
chmod 0640 "$BASE_PATH/shared/slots/blue.env" "$BASE_PATH/shared/slots/green.env"

if [[ -s "$VHOST" && ! -e "$VHOST_BACKUP" ]]; then cp -a "$VHOST" "$VHOST_BACKUP"; fi
install -o root -g root -m 0644 "$ROOT_DIR/packaging/nginx/print3dmaker.xyz.conf" "$VHOST"
ln -sfn "$BASE_PATH/shared/nginx/upstream-blue.conf" /etc/nginx/conf.d/printora-cloud-active.conf
printf 'blue\n' > "$BASE_PATH/shared/active-slot"
chown "$DEPLOY_USER:$DEPLOY_USER" "$BASE_PATH/shared/active-slot"

install -o root -g root -m 0440 "$ROOT_DIR/packaging/sudoers/printora-cloud-deploy" /etc/sudoers.d/printora-cloud-deploy
visudo -cf /etc/sudoers.d/printora-cloud-deploy
systemctl daemon-reload
systemctl enable --now printora-cloud-backup.timer
nginx -t
systemctl reload nginx
echo "Bootstrap instalado sem interromper a instância legada em 8069."
