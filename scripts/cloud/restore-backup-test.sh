#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
config="$base_path/shared/backup-target.conf"
[[ -s "$config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
set -a
source "$config"
set +a

restore_dir="$(mktemp -d /tmp/printora-restore-test.XXXXXX)"
trap 'rm -rf -- "$restore_dir"' EXIT
restic restore latest --tag printora-cloud-sqlite --target "$restore_dir"
database="$(find "$restore_dir" -type f -name printora.db -print -quit)"
[[ -n "$database" ]] || { echo "snapshot restaurado sem printora.db" >&2; exit 1; }
python3 - "$database" <<'PY'
import json
import sqlite3
import sys

connection = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
try:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    tables = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    versions = connection.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]
finally:
    connection.close()
print(json.dumps({"integrity": integrity, "tables": tables, "schema_versions": versions}))
if integrity != "ok" or tables == 0 or versions == 0:
    raise SystemExit("restore inválido")
PY
echo "restore externo validado em diretório isolado; aplicação não foi iniciada"
