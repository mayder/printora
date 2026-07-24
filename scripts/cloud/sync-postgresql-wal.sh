#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
cluster="${PRINTORA_POSTGRESQL_CLUSTER:-printora}"
port="${PRINTORA_POSTGRESQL_PORT:-5433}"
archive_dir="/var/lib/postgresql/16/$cluster-wal-archive"
backup_config="$base_path/shared/backup-target.conf"
state_dir="${PRINTORA_RECOVERY_STATE_DIR:-/var/lib/printora-cloud/recovery}"
state_file="$state_dir/wal-sync.json"
started_epoch="$(date +%s)"

[[ "$cluster" == "printora" && "$port" == "5433" ]] || {
  echo "cluster PostgreSQL inesperado" >&2
  exit 1
}
[[ -s "$backup_config" && -d "$archive_dir" ]] || {
  echo "origem ou destino de recuperação ausente" >&2
  exit 1
}
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
command -v flock >/dev/null || { echo "flock ausente" >&2; exit 1; }

install -d -o root -g root -m 0700 "$state_dir"
lock_file="${PRINTORA_RECOVERY_LOCK_FILE:-/run/printora-cloud/wal-sync.lock}"
install -d -o root -g root -m 0755 "$(dirname "$lock_file")"
exec 9>"$lock_file"
flock -n 9 || { echo "sincronização WAL já está em execução"; exit 0; }

latest_wal="$(
  find "$archive_dir" -maxdepth 1 -type f -regextype posix-extended \
    -regex '.*/[0-9A-F]{24}' -printf '%T@ %f\n' \
    | sort -n | tail -1 | awk '{print $2}'
)"
[[ "$latest_wal" =~ ^[0-9A-F]{24}$ && -s "$archive_dir/$latest_wal" ]] || {
  echo "arquivo WAL local válido ausente" >&2
  exit 1
}

previous_wal=""
if [[ -s "$state_file" ]]; then
  previous_wal="$(python3 - "$state_file" <<'PY'
import json
import pathlib
import sys

try:
    print(json.loads(pathlib.Path(sys.argv[1]).read_text()).get("uploaded_wal", ""))
except (OSError, ValueError):
    print("")
PY
)"
fi

set -a
source "$backup_config"
set +a
export RESTIC_CACHE_DIR="$base_path/shared/backup-cache"

uploaded_at=""
if [[ "$previous_wal" != "$latest_wal" ]]; then
  restic backup "$archive_dir" --tag printora-cloud-wal --host printora-cloud
  restic ls latest --tag printora-cloud-wal \
    | awk '{print $2}' | grep -Fxq "$archive_dir/$latest_wal"
  uploaded_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
else
  restic snapshots --tag printora-cloud-wal --latest 1 >/dev/null
  uploaded_at="$(python3 - "$state_file" <<'PY'
import json
import pathlib
import sys

print(json.loads(pathlib.Path(sys.argv[1]).read_text())["uploaded_at"])
PY
)"
fi

external_snapshot_count="$(
  restic snapshots --tag printora-cloud-wal --json \
    | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'
)"

checked_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
finished_epoch="$(date +%s)"
wal_count="$(find "$archive_dir" -maxdepth 1 -type f -regextype posix-extended -regex '.*/[0-9A-F]{24}' | wc -l | tr -d ' ')"
archive_bytes="$(du -sb "$archive_dir" | awk '{print $1}')"
state_next="$state_file.next"
python3 - "$state_next" "$checked_at" "$uploaded_at" "$latest_wal" \
  "$wal_count" "$archive_bytes" "$((finished_epoch - started_epoch))" \
  "$external_snapshot_count" <<'PY'
import json
import pathlib
import sys

payload = {
    "archive_bytes": int(sys.argv[6]),
    "checked_at": sys.argv[2],
    "duration_seconds": int(sys.argv[7]),
    "external_snapshot_count": int(sys.argv[8]),
    "status": "passed",
    "uploaded_at": sys.argv[3],
    "uploaded_wal": sys.argv[4],
    "wal_file_count": int(sys.argv[5]),
}
path = pathlib.Path(sys.argv[1])
path.write_text(json.dumps(payload, sort_keys=True) + "\n")
path.chmod(0o600)
PY
mv -f "$state_next" "$state_file"

echo "status=passed class=postgresql_wal external_copy=verified"
