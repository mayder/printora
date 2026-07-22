#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
release_sha="${1:-}"
confirmation="${2:-}"
[[ "$release_sha" =~ ^[0-9a-f]{7,64}$ ]] || { echo "SHA de release inválido" >&2; exit 1; }
release_dir="$base_path/releases/$release_sha"
[[ -x "$release_dir/venv/bin/python" ]] || { echo "venv da release ausente" >&2; exit 1; }
set -a
source /etc/printora-cloud/postgresql.env
set +a
exec "$release_dir/venv/bin/python" \
  /usr/local/libexec/printora-cloud/cutover-postgresql.py \
  "$release_sha" "$confirmation"
