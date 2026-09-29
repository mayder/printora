#!/usr/bin/env bash
set -euo pipefail
[[ "$(id -u)" -eq 0 ]] || { echo 'root_required' >&2; exit 1; }
set -a
source /var/www/print3dmaker.xyz/shared/backup-target.conf
set +a
export RESTIC_CACHE_DIR=/var/www/print3dmaker.xyz/shared/backup-cache
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/retain-postgresql-wal.py" "$@"
