#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"

require_root
failures=0
check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "check=$label status=ok"
  else
    echo "check=$label status=failed"
    failures=$((failures + 1))
  fi
}

validate_backup_target() {
  local config="$PRINTORA_BASE_PATH/shared/backup-target.conf"
  [[ "$(stat -c '%a' "$config")" == "600" ]] || return 1
  [[ "$(stat -c '%U' "$config")" == "deploy" ]] || return 1
  python3 - "$config" <<'PY'
import sys

values = {}
for raw_line in open(sys.argv[1], encoding="utf-8"):
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip().strip("'\"")
repository = values.get("RESTIC_REPOSITORY", "")
password_file = values.get("RESTIC_PASSWORD_FILE", "")
external_prefixes = ("s3:", "sftp:", "rest:", "azure:", "gs:", "b2:", "rclone:")
if not repository.startswith(external_prefixes) or not password_file.startswith("/"):
    raise SystemExit(1)
PY
}

check python python3 --version
check nginx nginx -t
check systemd systemctl cat printora-cloud@.service
check clock bash -c '[[ "$(timedatectl show --property=NTPSynchronized --value)" == "yes" ]]'
check base_writable test -w "$PRINTORA_BASE_PATH"
check data_writable test -w "$PRINTORA_BASE_PATH/shared/data"
check blue_port bash -c '! ss -ltnH "sport = :8069" | grep -q . || systemctl is-active --quiet printora-cloud@blue.service || systemctl is-active --quiet printora-cloud.service'
check green_port bash -c '! ss -ltnH "sport = :8070" | grep -q . || systemctl is-active --quiet printora-cloud@green.service'
check certificate test -s /etc/letsencrypt/live/print3dmaker.xyz/fullchain.pem
check logrotate test -s /etc/logrotate.d/printora-cloud
check restic restic version
check backup_target validate_backup_target

[[ "$failures" -eq 0 ]] || fail "$failures item(ns) de preflight falharam"
