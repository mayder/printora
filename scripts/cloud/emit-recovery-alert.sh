#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
event="${1:-unknown}"
[[ "$event" =~ ^[A-Za-z0-9@_.:-]+$ ]] || { echo "evento inválido" >&2; exit 1; }

state_dir="${PRINTORA_RECOVERY_STATE_DIR:-/var/lib/printora-cloud/recovery}"
config=/etc/printora-cloud/recovery-alert.env
install -d -o root -g root -m 0700 "$state_dir"
occurred_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
delivery=journal

logger -p daemon.crit -t printora-cloud-recovery \
  "status=failed event=$event owner=operations"

if [[ -s "$config" ]]; then
  set -a
  source "$config"
  set +a
  if [[ -n "${PRINTORA_RECOVERY_ALERT_WEBHOOK_URL:-}" ]]; then
    payload="$(python3 - "$event" "$occurred_at" <<'PY'
import json
import sys

print(json.dumps({
    "event": sys.argv[1],
    "occurred_at": sys.argv[2],
    "owner": "operations",
    "service": "printora-cloud-recovery",
    "status": "failed",
}, sort_keys=True))
PY
)"
    if curl --fail --silent --max-time 10 \
      -H 'Content-Type: application/json' \
      --data "$payload" \
      "$PRINTORA_RECOVERY_ALERT_WEBHOOK_URL" >/dev/null 2>&1; then
      delivery=journal_and_webhook
    else
      delivery=journal_webhook_failed
    fi
  fi
fi

state_next="$state_dir/last-alert.json.next"
python3 - "$state_next" "$event" "$occurred_at" "$delivery" <<'PY'
import json
import pathlib
import sys

payload = {
    "delivery": sys.argv[4],
    "event": sys.argv[2],
    "occurred_at": sys.argv[3],
    "owner": "operations",
    "status": "recorded",
}
path = pathlib.Path(sys.argv[1])
path.write_text(json.dumps(payload, sort_keys=True) + "\n")
path.chmod(0o600)
PY
mv -f "$state_next" "$state_dir/last-alert.json"
echo "status=recorded owner=operations delivery=$delivery"
