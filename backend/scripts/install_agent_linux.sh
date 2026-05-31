#!/usr/bin/env bash
set -euo pipefail

MODE="preflight"
ASSUME_YES=0
PREFIX="${PRINTORA_AGENT_PREFIX:-/usr/local}"
CONFIG_DIR="${PRINTORA_AGENT_CONFIG_DIR:-/etc/printora-agent}"
STATE_DIR="${PRINTORA_AGENT_STATE_DIR:-/var/lib/printora-agent}"
LOG_DIR="${PRINTORA_AGENT_LOG_DIR:-/var/log/printora-agent}"
SERVICE_NAME="${PRINTORA_AGENT_SERVICE_NAME:-printora-agent}"
SERVICE_USER="${PRINTORA_AGENT_SERVICE_USER:-printora-agent}"
MOONRAKER_URL="${PRINTORA_MOONRAKER_URL:-http://127.0.0.1:7125}"
API_BASE="${PRINTORA_API_BASE:-}"
PAIRING_TOKEN="${PRINTORA_PAIRING_TOKEN:-}"
AGENT_VERSION="${PRINTORA_AGENT_VERSION:-0.1.0}"
BIN_URL="${PRINTORA_AGENT_BIN_URL:-}"
LOCAL_BIN="${PRINTORA_AGENT_BIN:-}"
TEST_MODE="${PRINTORA_AGENT_INSTALL_TEST_MODE:-0}"

usage() {
  cat <<'USAGE'
Uso:
  install-printora-agent.sh --preflight
  install-printora-agent.sh --apply --yes
  install-printora-agent.sh --uninstall

Variáveis:
  PRINTORA_API_BASE         URL da API Printora
  PRINTORA_PAIRING_TOKEN    token curto de pareamento
  PRINTORA_MOONRAKER_URL    URL local do Moonraker
  PRINTORA_AGENT_BIN_URL    URL do binário do agente
  PRINTORA_AGENT_BIN        binário local já baixado
USAGE
}

log() { printf '[printora-agent-install] %s\n' "$*"; }
fail() { printf '[printora-agent-install] ERRO: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
redacted_token_status() { [[ -n "$PAIRING_TOKEN" ]] && printf 'configurado' || printf 'ausente'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preflight|--dry-run) MODE="preflight" ;;
    --apply) MODE="apply" ;;
    --uninstall) MODE="uninstall" ;;
    --yes|-y) ASSUME_YES=1 ;;
    --help|-h) usage; exit 0 ;;
    *) fail "argumento desconhecido: $1" ;;
  esac
  shift
done

require_linux() {
  if [[ "$TEST_MODE" == "1" ]]; then
    return
  fi
  [[ "$(uname -s)" == "Linux" ]] || fail "este instalador suporta Linux/Raspberry/BTT Pi"
}

require_systemd() {
  if [[ "$TEST_MODE" == "1" ]]; then
    return
  fi
  [[ -d /run/systemd/system ]] && have systemctl || fail "systemd não detectado"
}

require_root() {
  if [[ "$TEST_MODE" == "1" ]]; then
    return
  fi
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "rode com sudo para instalar serviço e diretórios"
}

preflight() {
  require_linux
  log "api: ${API_BASE:-ausente}"
  log "token: $(redacted_token_status)"
  log "moonraker: $MOONRAKER_URL"
  have curl || fail "curl ausente"
  have python3 || fail "python3 ausente para processar troca segura do token"
  have install || fail "install ausente"
  require_systemd
  if curl -fsS --max-time 3 "$MOONRAKER_URL/server/info" >/dev/null 2>&1; then
    log "moonraker: ok"
  else
    log "moonraker: aviso, endpoint local não respondeu"
  fi
  log "preflight concluído"
}

confirm_apply() {
  [[ "$ASSUME_YES" == "1" ]] && return
  fail "reexecute com --yes depois de revisar o preflight"
}

install_binary() {
  local target="$PREFIX/bin/printora-agent"
  if [[ -n "$LOCAL_BIN" ]]; then
    [[ -x "$LOCAL_BIN" ]] || fail "PRINTORA_AGENT_BIN não é executável"
    install -m 0755 "$LOCAL_BIN" "$target"
    return
  fi
  if [[ -n "$BIN_URL" ]]; then
    curl -fsSL "$BIN_URL" -o "$target.tmp"
    install -m 0755 "$target.tmp" "$target"
    rm -f "$target.tmp"
    return
  fi
  if have printora-agent; then
    install -m 0755 "$(command -v printora-agent)" "$target"
    return
  fi
  fail "binário do agente ausente; informe PRINTORA_AGENT_BIN_URL ou PRINTORA_AGENT_BIN"
}

exchange_token() {
  [[ -n "$API_BASE" ]] || fail "PRINTORA_API_BASE obrigatório"
  [[ -n "$PAIRING_TOKEN" ]] || fail "PRINTORA_PAIRING_TOKEN obrigatório"
  local stable_id payload response
  stable_id="printora-$(hostname)-$(cat /etc/machine-id 2>/dev/null | cut -c1-12 || date +%s)"
  payload="$(python3 - "$PAIRING_TOKEN" "$stable_id" "$AGENT_VERSION" <<'PY'
import json
import platform
import sys

print(json.dumps({
    "pairing_token": sys.argv[1],
    "stable_id": sys.argv[2],
    "agent_version": sys.argv[3],
    "platform": "linux/" + platform.machine(),
    "capabilities": {"installer": True, "systemd": True, "websocket": True, "polling": True},
}))
PY
)"
  response="$(curl -fsS -H 'Content-Type: application/json' -d "$payload" "$API_BASE/api/agent/pairing/exchange")"
  python3 - "$response" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
credential = payload.get("credential")
if not credential:
    raise SystemExit("resposta sem credential")
print(credential)
PY
}

write_config() {
  local credential="$1"
  install -d -m 0750 "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR"
  printf '%s\n' "$credential" > "$CONFIG_DIR/credential"
  chmod 0600 "$CONFIG_DIR/credential"
  python3 - "$API_BASE" "$MOONRAKER_URL" "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR" <<'PY' > "$CONFIG_DIR/config.json"
import json
import sys

api_base, moonraker_url, config_dir, state_dir, log_dir = sys.argv[1:]
print(json.dumps({
    "api_base_url": api_base,
    "moonraker_url": moonraker_url,
    "credential_file": config_dir + "/credential",
    "queue_file": state_dir + "/queue.jsonl",
    "log_file": log_dir + "/agent.log",
    "interval_seconds": 10,
    "timeout_seconds": 5,
    "websocket_enabled": True,
    "polling_enabled": True,
    "max_payload_bytes": 65536,
    "update_enabled": True,
    "update_check_interval_seconds": 3600,
    "update_manifest_url": api_base + "/api/agent/update/manifest",
    "update_state_file": state_dir + "/update-state.json",
    "update_staging_dir": state_dir + "/updates",
    "agent_binary_path": "/usr/local/bin/printora-agent",
    "agent_service_name": "printora-agent",
    "allow_service_restart": True,
}, indent=2))
PY
  chmod 0600 "$CONFIG_DIR/config.json"
}

install_service() {
  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
  fi
  chown -R "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR"
  cat > "/etc/systemd/system/$SERVICE_NAME.service" <<SERVICE
[Unit]
Description=Printora Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$PREFIX/bin/printora-agent -config $CONFIG_DIR/config.json run
Restart=always
RestartSec=5
User=$SERVICE_USER
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE
  systemctl daemon-reload
  systemctl enable --now "$SERVICE_NAME"
}

apply_install() {
  require_linux
  require_root
  require_systemd
  confirm_apply
  preflight
  install_binary
  local credential
  credential="$(exchange_token)"
  write_config "$credential"
  install_service
  log "instalação concluída; valide no Printora se o heartbeat chegou"
}

uninstall() {
  require_root
  if have systemctl; then
    systemctl disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
    rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload >/dev/null 2>&1 || true
  fi
  rm -f "$PREFIX/bin/printora-agent"
  log "serviço e binário removidos"
  log "dados preservados em $CONFIG_DIR, $STATE_DIR e $LOG_DIR"
  log "remova esses diretórios manualmente somente se tiver certeza"
}

case "$MODE" in
  preflight) preflight ;;
  apply) apply_install ;;
  uninstall) uninstall ;;
  *) fail "modo inválido: $MODE" ;;
esac
