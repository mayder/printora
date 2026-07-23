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
custody_id = values.get("PRINTORA_RECOVERY_CUSTODY_ID", "")
external_prefixes = ("s3:", "sftp:", "rest:", "azure:", "gs:", "b2:", "rclone:")
if not repository.startswith(external_prefixes) or not password_file.startswith("/") or not custody_id:
    raise SystemExit(1)
PY
}

validate_backup_repository() {
  local config="$PRINTORA_BASE_PATH/shared/backup-target.conf"
  timeout 30 sudo -u deploy bash -c '
    set -euo pipefail
    set -a
    source "$1"
    set +a
    restic snapshots >/dev/null
  ' bash "$config"
}

validate_resource_budget() {
  local available_memory_kb available_disk_kb available_inodes
  available_memory_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
  available_disk_kb="$(df -Pk "$PRINTORA_BASE_PATH" | awk 'NR == 2 {print $4}')"
  available_inodes="$(df -Pi "$PRINTORA_BASE_PATH" | awk 'NR == 2 {print $4}')"
  [[ "$available_memory_kb" -ge 2097152 ]]
  [[ "$available_disk_kb" -ge 20971520 ]]
  [[ "$available_inodes" -ge 1000000 ]]
}

validate_postgresql_environment() {
  local config=/etc/printora-cloud/postgresql.env
  [[ "$(stat -c '%a' "$config")" == "640" ]] || return 1
  [[ "$(stat -c '%U:%G' "$config")" == "root:deploy" ]] || return 1
  bash -c '
    set -euo pipefail
    set -a
    source "$1"
    set +a
    [[ "${PRINTORA_DATABASE_URL:-}" == postgresql://*@127.0.0.1:5433/printora_cloud ]]
  ' bash "$config"
}

validate_postgresql_runtime() {
  systemctl is-active --quiet postgresql@16-printora.service
  pg_isready -q -h 127.0.0.1 -p 5433 -d printora_cloud
  [[ -d /var/lib/postgresql/16/printora-wal-archive ]]
  [[ "$(runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc \
    "SELECT current_setting('data_checksums') || ':' || current_setting('archive_mode')")" == "on:on" ]]
  [[ "$(runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc \
    "SELECT has_table_privilege('printora_analytics','analytics_events','UPDATE')::int || ':' ||
            has_table_privilege('printora_analytics','auth_users','SELECT')::int")" == "1:0" ]]
}

validate_durable_workers() {
  local queue config
  test -x /usr/local/libexec/printora-cloud/start-worker.sh
  systemctl cat printora-cloud-worker@.service >/dev/null
  systemctl cat printora-cloud-workers.target >/dev/null
  systemctl cat printora-cloud-intelligence.service >/dev/null
  for queue in outbox critical default bulk; do
    config="/etc/printora-cloud/workers/$queue.env"
    [[ "$(stat -c '%a:%U:%G' "$config")" == "640:root:deploy" ]] || return 1
    grep -Eq '^PRINTORA_WORKER_CONCURRENCY=[1-9][0-9]*$' "$config" || return 1
  done
}

validate_application_slots() {
  local slot config expected_port
  for slot in blue green replica; do
    config="$PRINTORA_BASE_PATH/shared/slots/$slot.env"
    case "$slot" in
      blue) expected_port=8069 ;;
      green) expected_port=8070 ;;
      replica) expected_port=8071 ;;
    esac
    [[ "$(stat -c '%a:%U:%G' "$config")" == "640:deploy:deploy" ]] || return 1
    grep -qx "PRINTORA_PORT=$expected_port" "$config" || return 1
    grep -qx "PRINTORA_SLOT=$slot" "$config" || return 1
    grep -qx "PRINTORA_RUNTIME_PROFILE=cloud" "$config" || return 1
  done
}

validate_recomposable_redis() {
  local config=/etc/printora-cloud/redis.env
  [[ "$(stat -c '%a:%U:%G' "$config")" == "640:root:deploy" ]] || return 1
  grep -qx 'PRINTORA_REDIS_URL=unix:///run/redis-printora/redis.sock?db=0' "$config"
  systemctl is-active --quiet redis-printora.service
  [[ "$(redis-cli -s /run/redis-printora/redis.sock ping)" == "PONG" ]]
  redis-cli -s /run/redis-printora/redis.sock INFO persistence | grep -q '^aof_enabled:0'
  grep -qx 'save ""' /etc/redis/printora.conf
  grep -qx 'appendonly no' /etc/redis/printora.conf
  grep -qx 'maxmemory-policy allkeys-lru' /etc/redis/printora.conf
}

validate_object_storage() {
  local config=/etc/printora-cloud/object-storage.env
  [[ "$(stat -c '%a:%U:%G' "$config")" == "640:root:deploy" ]] || return 1
  grep -qx 'PRINTORA_OBJECT_STORAGE_MODE=s3' "$config"
  grep -qx 'PRINTORA_OBJECT_STORAGE_ENDPOINT_URL=http://127.0.0.1:9100' "$config"
  systemctl is-active --quiet minio-printora.service
  curl -fsS --max-time 2 http://127.0.0.1:9100/minio/health/ready >/dev/null
  [[ -x /usr/local/libexec/printora-cloud/run-object-storage-tool.sh ]]
}

check python python3 --version
check nginx nginx -t
check systemd systemctl cat printora-cloud@.service
check clock bash -c '[[ "$(timedatectl show --property=NTPSynchronized --value)" == "yes" ]]'
check base_writable sudo -u deploy test -w "$PRINTORA_BASE_PATH"
check data_writable sudo -u deploy test -w "$PRINTORA_BASE_PATH/shared/data"
check blue_port bash -c '! ss -ltnH "sport = :8069" | grep -q . || systemctl is-active --quiet printora-cloud@blue.service'
check green_port bash -c '! ss -ltnH "sport = :8070" | grep -q . || systemctl is-active --quiet printora-cloud@green.service'
check replica_port bash -c '! ss -ltnH "sport = :8071" | grep -q . || systemctl is-active --quiet printora-cloud@replica.service'
check certificate test -s /etc/letsencrypt/live/print3dmaker.xyz/fullchain.pem
check logrotate test -s /etc/logrotate.d/printora-cloud
check restic restic version
check backup_target validate_backup_target
check backup_repository validate_backup_repository
check resource_budget validate_resource_budget
check postgresql_environment validate_postgresql_environment
check postgresql_runtime validate_postgresql_runtime
check application_slots validate_application_slots
check durable_workers validate_durable_workers
check recomposable_redis validate_recomposable_redis
check object_storage validate_object_storage

[[ "$failures" -eq 0 ]] || fail "$failures item(ns) de preflight falharam"
