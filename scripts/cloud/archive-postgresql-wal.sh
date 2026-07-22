#!/usr/bin/env bash
set -euo pipefail

source_wal="${1:-}"
wal_name="${2:-}"
archive_dir="${PRINTORA_POSTGRESQL_WAL_ARCHIVE:-/var/lib/postgresql/16/printora-wal-archive}"
[[ -f "$source_wal" ]] || { echo "segmento WAL de origem ausente" >&2; exit 1; }
[[ "$wal_name" =~ ^([0-9A-F]{24}(\.[0-9A-F]{8}\.backup)?|[0-9A-F]{8}\.history)$ ]] || {
  echo "nome de WAL inválido" >&2
  exit 1
}
target="$archive_dir/$wal_name"
[[ -s "$target" ]] && exit 0
temporary="$archive_dir/.$wal_name.partial"
cleanup() { rm -f -- "$temporary"; }
trap cleanup EXIT
cp -- "$source_wal" "$temporary"
chmod 0600 "$temporary"
sync "$temporary"
mv -f -- "$temporary" "$target"
trap - EXIT
