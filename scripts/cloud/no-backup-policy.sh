#!/usr/bin/env bash
# DEC-20261101-01: no automatic backup/PITR for this Printora installation.
# Source only. Never change database settings or restart PostgreSQL here.

printora_recovery_names=(backup wal-sync wal-retention restore-test recovery-monitor)

disable_recovery_units() {
  local unit_dir="${1:-/etc/systemd/system}" name suffix unit
  for name in "${printora_recovery_names[@]}"; do
    for suffix in timer service; do
      unit="printora-cloud-$name.$suffix"
      if systemctl cat "$unit" >/dev/null 2>&1; then
        systemctl stop "$unit"
        if [[ "$suffix" == timer && "$(systemctl is-enabled "$unit" 2>/dev/null || true)" != masked ]]; then
          systemctl disable "$unit"
        fi
      fi
      # Exact allowlist only; do not overwrite a mask with a packaged unit.
      ln -sfn /dev/null "$unit_dir/$unit"
    done
  done
  systemctl daemon-reload
}

validate_no_backup_policy() {
  local name suffix unit state
  for name in "${printora_recovery_names[@]}"; do
    for suffix in timer service; do
      unit="printora-cloud-$name.$suffix"
      [[ "$(systemctl is-enabled "$unit" 2>/dev/null || true)" == masked ]] || return 1
      state="$(systemctl show "$unit" --property=ActiveState --value)" || return 1
      [[ "$state" == inactive || "$state" == failed ]] || return 1
    done
  done
  state="$(runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc \
    "SELECT current_setting('data_checksums') || ':' || current_setting('archive_mode') || ':' ||
      extract(epoch FROM current_setting('archive_timeout')::interval)::int || ':' ||
      current_setting('fsync') || ':' || current_setting('full_page_writes') || ':' ||
      current_setting('synchronous_commit') || ':' ||
      (SELECT count(*) FROM pg_stat_replication) || ':' ||
      (SELECT count(*) FROM pg_replication_slots)")" || return 1
  [[ "$state" == 'on:off:0:on:on:on:0:0' ]] || return 1
  echo 'recovery_mode=disabled_by_owner decision=DEC-20261101-01 backup_available=false'
}
