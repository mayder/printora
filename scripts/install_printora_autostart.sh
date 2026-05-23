#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

MODE="plan"
YES="false"
PORT="${PRINTORA_PORT:-8085}"
HOST="${PRINTORA_HOST:-0.0.0.0}"
DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
HOST_NAME="${HOST_NAME:-printora}"

usage() {
  cat <<'USAGE'
Uso:
  scripts/install_printora_autostart.sh --plan
  scripts/install_printora_autostart.sh --apply --yes

Configura o Printora para subir no boot:
  Android/Termux: Termux:Boot + tmux
  Linux/Raspberry: systemd com Restart=always
  macOS: launchd com KeepAlive
USAGE
}

is_termux() {
  [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]]
}

platform_kind() {
  if is_termux; then
    echo "android_termux"
  else
    mpl_os
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --apply) MODE="apply"; shift ;;
    --yes) YES="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento inválido: $1" >&2; usage >&2; exit 2 ;;
  esac
done

kind="$(platform_kind)"
cat <<PLAN
Printora autostart
mode=$MODE
platform=$kind
root_dir=$ROOT_DIR
data_dir=$DATA_DIR
port=$PORT
host=$HOST
android_boot=$HOME/.termux/boot/start-printora
linux_service=/etc/systemd/system/printora.service
macos_plist=$HOME/Library/LaunchAgents/com.printora.app.plist
PLAN

if [[ "$MODE" == "plan" ]]; then
  exit 0
fi

[[ "$YES" == "true" || "${PRINTORA_ASSUME_YES:-}" == "1" ]] || {
  echo "--apply exige --yes." >&2
  exit 1
}

mkdir -p "$DATA_DIR"

case "$kind" in
  android_termux)
    mkdir -p "$HOME/.termux/boot" "$DATA_DIR/logs"
    if command -v pkg >/dev/null 2>&1; then
      yes | pkg install tmux termux-api >/dev/null || true
    fi
    cat >"$HOME/.termux/boot/start-printora" <<SH
#!/data/data/com.termux/files/usr/bin/sh
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
mkdir -p "$DATA_DIR/logs"
cd "$ROOT_DIR" || exit 0
PRINTORA_DATA_DIR="$DATA_DIR" PRINTORA_PORT="$PORT" HTTP_PORT="$PORT" PUBLIC_PORT="$PORT" HOST_NAME="$HOST_NAME" \\
  scripts/android_start_printora.sh >> "$DATA_DIR/logs/boot.log" 2>&1
SH
    chmod +x "$HOME/.termux/boot/start-printora"
    echo "Termux:Boot configurado. Abra o app Termux:Boot uma vez e remova otimização de bateria do Termux/Termux:Boot."
    ;;
  linux)
    if ! mpl_has_systemd; then
      echo "systemd não detectado neste Linux." >&2
      exit 1
    fi
    service_tmp="$(mktemp)"
    cat >"$service_tmp" <<SERVICE
[Unit]
Description=Printora
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${ROOT_DIR}
Environment=PRINTORA_DATA_DIR=${DATA_DIR}
Environment=PRINTORA_HOST=${HOST}
Environment=PRINTORA_PORT=${PORT}
ExecStart=${ROOT_DIR}/scripts/run_app.sh --foreground --no-open
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE
    sudo cp "$service_tmp" /etc/systemd/system/printora.service
    rm -f "$service_tmp"
    sudo systemctl daemon-reload
    sudo systemctl enable printora.service
    sudo systemctl restart printora.service
    ;;
  macos)
    mkdir -p "$HOME/Library/LaunchAgents" "$DATA_DIR/logs"
    cat >"$HOME/Library/LaunchAgents/com.printora.app.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.printora.app</string>
  <key>ProgramArguments</key>
  <array>
    <string>${ROOT_DIR}/scripts/run_app.sh</string>
    <string>--foreground</string>
    <string>--no-open</string>
  </array>
  <key>WorkingDirectory</key><string>${ROOT_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PRINTORA_DATA_DIR</key><string>${DATA_DIR}</string>
    <key>PRINTORA_HOST</key><string>${HOST}</string>
    <key>PRINTORA_PORT</key><string>${PORT}</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>${DATA_DIR}/logs/launchd.log</string>
  <key>StandardErrorPath</key><string>${DATA_DIR}/logs/launchd.err.log</string>
</dict>
</plist>
PLIST
    launchctl unload "$HOME/Library/LaunchAgents/com.printora.app.plist" >/dev/null 2>&1 || true
    launchctl load "$HOME/Library/LaunchAgents/com.printora.app.plist"
    ;;
  *)
    echo "Plataforma sem autostart suportado: $kind" >&2
    exit 1
    ;;
esac

echo "Autostart do Printora configurado."
