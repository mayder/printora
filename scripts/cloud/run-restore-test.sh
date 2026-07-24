#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }

state_dir="${PRINTORA_RECOVERY_STATE_DIR:-/var/lib/printora-cloud/recovery}"
state_file="$state_dir/restore-test.json"
private_log="$state_dir/restore-test-private.log"
restore_script=/usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
started_epoch="$(date +%s)"
install -d -o root -g root -m 0700 "$state_dir"
[[ -x "$restore_script" ]] || { echo "executor de restore ausente" >&2; exit 1; }

set +e
timeout 900 "$restore_script" >"$private_log" 2>&1
result=$?
set -e
chmod 0600 "$private_log"
finished_epoch="$(date +%s)"
duration="$((finished_epoch - started_epoch))"

if [[ "$result" -ne 0 ]]; then
  echo "restore isolado falhou; diagnóstico preservado em log privado" >&2
  exit "$result"
fi
[[ "$duration" -le 900 ]] || { echo "restore excedeu o RTO" >&2; exit 1; }

state_next="$state_file.next"
python3 - "$state_next" "$duration" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

payload = {
    "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "duration_seconds": int(sys.argv[2]),
    "isolated": True,
    "status": "passed",
    "validation": [
        "configuration_checksums",
        "foreign_keys",
        "object_checksums",
        "schema_revisions",
        "search_rebuild",
        "wal_replay",
    ],
}
path = pathlib.Path(sys.argv[1])
path.write_text(json.dumps(payload, sort_keys=True) + "\n")
path.chmod(0o600)
PY
mv -f "$state_next" "$state_file"
echo "status=passed restore=isolated rto_seconds=$duration"
