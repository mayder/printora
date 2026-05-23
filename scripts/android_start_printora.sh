#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$HOME/Printora}"
HTTP_PORT="${HTTP_PORT:-${PRINTORA_PORT:-8085}}"
PUBLIC_PORT="${PUBLIC_PORT:-$HTTP_PORT}"
HOST_NAME="${HOST_NAME:-printora}"
DATA_DIR="${PRINTORA_DATA_DIR:-$HOME/.local/share/printora}"
MOONRAKER_URL="${PRINTORA_MOONRAKER_URL:-http://voron.local:7125}"

cd "$ROOT_DIR"

tmux kill-session -t printora 2>/dev/null || true
tmux kill-session -t printora-mdns 2>/dev/null || true

tmux new-session -d -s printora "cd '$ROOT_DIR/backend' && export PRINTORA_DATA_DIR='$DATA_DIR' PRINTORA_MOONRAKER_URL='$MOONRAKER_URL' && . .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port '$HTTP_PORT'"

start_mdns() {
  tmux new-session -d -s printora-mdns "cd '$ROOT_DIR' && python scripts/android_mdns_printora.py --name '$HOST_NAME' --port '$PUBLIC_PORT'"
}

start_mdns
sleep 2
if ! tmux has-session -t printora-mdns 2>/dev/null; then
  start_mdns
fi

bash ./check.sh
if [[ "$PUBLIC_PORT" == "80" ]]; then
  echo "http://${HOST_NAME}.local/"
else
  echo "http://${HOST_NAME}.local:${PUBLIC_PORT}/"
fi
