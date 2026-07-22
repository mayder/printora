#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
config="$base_path/shared/backup-target.conf"
database="$base_path/shared/data/printora.db"
[[ -s "$config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
[[ -s "$database" ]] || { echo "banco SQLite ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
set -a
source "$config"
set +a

work_dir="$(mktemp -d /tmp/printora-backup.XXXXXX)"
trap 'rm -rf -- "$work_dir"' EXIT
snapshot="$work_dir/printora.db"
python3 - "$database" "$snapshot" <<'PY'
import sqlite3
import sys

source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
try:
    source.backup(target)
finally:
    target.close()
    source.close()
PY
python3 - "$snapshot" <<'PY'
import sqlite3
import sys

connection = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
try:
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
finally:
    connection.close()
if result != "ok":
    raise SystemExit(f"integrity_check falhou: {result}")
PY
restic backup "$snapshot" --tag printora-cloud-sqlite --host printora-cloud
echo "backup externo criptografado concluído; retenção exige execução supervisionada separada"
