#!/usr/bin/env bash
set -euo pipefail

MODE="preflight"
ASSUME_YES=0
PREFIX="${PRINTORA_AGENT_PREFIX:-/usr/local}"
CONFIG_DIR="${PRINTORA_AGENT_CONFIG_DIR:-/etc/printora-agent}"
STATE_DIR="${PRINTORA_AGENT_STATE_DIR:-/var/lib/printora-agent}"
LOG_DIR="${PRINTORA_AGENT_LOG_DIR:-/var/log/printora-agent}"
SERVICE_NAME="${PRINTORA_AGENT_SERVICE_NAME:-printora-agent}"
SERVICE_USER="${PRINTORA_AGENT_SERVICE_USER:-root}"
MOONRAKER_URL="${PRINTORA_MOONRAKER_URL:-http://127.0.0.1:7125}"
API_BASE="${PRINTORA_API_BASE:-}"
PAIRING_TOKEN="${PRINTORA_PAIRING_TOKEN:-}"
AGENT_VERSION="${PRINTORA_AGENT_VERSION:-0.1.17}"
BIN_URL="${PRINTORA_AGENT_BIN_URL:-}"
LOCAL_BIN="${PRINTORA_AGENT_BIN:-}"
AGENT_SHA256="${PRINTORA_AGENT_SHA256:-}"
AGENT_SIGNATURE="${PRINTORA_AGENT_SIGNATURE:-}"
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

extract_error_detail() {
  local body_file="$1"
  python3 - "$body_file" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(errors="replace").strip() if path.exists() else ""
if not text:
    raise SystemExit(0)
try:
    payload = json.loads(text)
except json.JSONDecodeError:
    raise SystemExit(0)
detail = payload.get("detail") if isinstance(payload, dict) else None
if isinstance(detail, str) and detail.strip():
    print(detail.strip())
PY
}

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
  local target="$PREFIX/bin/printora-agent" candidate=""
  if [[ -n "$LOCAL_BIN" ]]; then
    [[ -x "$LOCAL_BIN" ]] || fail "PRINTORA_AGENT_BIN não é executável"
    candidate="$LOCAL_BIN"
  elif [[ -n "$BIN_URL" ]]; then
    candidate="$target.tmp"
    curl -fsSL --retry 5 --retry-delay 2 --connect-timeout 10 "$BIN_URL" -o "$candidate"
  elif have printora-agent; then
    candidate="$(command -v printora-agent)"
  else
    fail "binário do agente ausente; informe PRINTORA_AGENT_BIN_URL ou PRINTORA_AGENT_BIN"
  fi
  verify_release "$candidate"
  install -m 0755 "$candidate" "$target"
  [[ "$candidate" == "$target.tmp" ]] && rm -f "$candidate"
}

verify_release() {
  local candidate="$1" actual
  [[ -n "$AGENT_SHA256" ]] || fail "PRINTORA_AGENT_SHA256 obrigatório"
  [[ -n "$AGENT_SIGNATURE" ]] || fail "PRINTORA_AGENT_SIGNATURE obrigatória"
  actual="$(python3 - "$candidate" <<'PY'
import hashlib
import pathlib
import sys

print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
  [[ "$actual" == "$AGENT_SHA256" ]] || fail "checksum do agente não confere"
  if ! python3 - "$actual" "$AGENT_SIGNATURE" <<'PY'
import base64
import binascii
import hashlib
import sys

PUBLIC_KEY = base64.b64decode("dK8RtUcm2hdrv0CFCNMFago1e+8RmT3ab9fbDyK8hmg=")
FIELD = 2**255 - 19
ORDER = 2**252 + 27742317777372353535851937790883648493


def inverse(value):
    return pow(value, FIELD - 2, FIELD)


D = (-121665 * inverse(121666)) % FIELD
SQRT_M1 = pow(2, (FIELD - 1) // 4, FIELD)


def recover_x(y):
    xx = (y * y - 1) * inverse(D * y * y + 1)
    x = pow(xx, (FIELD + 3) // 8, FIELD)
    if (x * x - xx) % FIELD:
        x = (x * SQRT_M1) % FIELD
    if (x * x - xx) % FIELD:
        raise ValueError("ponto Ed25519 inválido")
    return x


def decode_point(encoded):
    if len(encoded) != 32:
        raise ValueError("ponto Ed25519 inválido")
    y = int.from_bytes(encoded, "little") & ((1 << 255) - 1)
    if y >= FIELD:
        raise ValueError("ponto Ed25519 não canônico")
    x = recover_x(y)
    if (x & 1) != (encoded[31] >> 7):
        x = FIELD - x
    if (-x * x + y * y - 1 - D * x * x * y * y) % FIELD:
        raise ValueError("ponto Ed25519 fora da curva")
    return x, y


def add_points(left, right):
    x1, y1 = left
    x2, y2 = right
    product = D * x1 * x2 * y1 * y2
    return (
        (x1 * y2 + x2 * y1) * inverse(1 + product) % FIELD,
        (y1 * y2 + x1 * x2) * inverse(1 - product) % FIELD,
    )


def multiply_point(point, scalar):
    result = (0, 1)
    current = point
    while scalar:
        if scalar & 1:
            result = add_points(result, current)
        current = add_points(current, current)
        scalar >>= 1
    return result


BASE_Y = 4 * inverse(5) % FIELD
BASE_X = recover_x(BASE_Y)
if BASE_X & 1:
    BASE_X = FIELD - BASE_X
BASE_POINT = (BASE_X, BASE_Y)

message = sys.argv[1].encode()
try:
    signature = base64.b64decode(sys.argv[2], validate=True)
except binascii.Error as error:
    raise SystemExit("assinatura Ed25519 inválida") from error
if len(signature) != 64:
    raise SystemExit("assinatura Ed25519 inválida")
try:
    public_point = decode_point(PUBLIC_KEY)
    signature_point = decode_point(signature[:32])
except ValueError as error:
    raise SystemExit(str(error)) from error
scalar = int.from_bytes(signature[32:], "little")
if scalar >= ORDER:
    raise SystemExit("assinatura Ed25519 não canônica")
challenge = int.from_bytes(
    hashlib.sha512(signature[:32] + PUBLIC_KEY + message).digest(),
    "little",
) % ORDER
if multiply_point(BASE_POINT, scalar) != add_points(
    signature_point,
    multiply_point(public_point, challenge),
):
    raise SystemExit("assinatura Ed25519 não confere")
PY
  then
    fail "assinatura do agente não confere"
  fi
}

exchange_token() {
  [[ -n "$API_BASE" ]] || fail "PRINTORA_API_BASE obrigatório"
  [[ -n "$PAIRING_TOKEN" ]] || fail "PRINTORA_PAIRING_TOKEN obrigatório"
  local stable_id payload response_file http_status curl_status detail
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
  response_file="$(mktemp)"
  curl_status=0
  http_status="$(
    curl -sS -o "$response_file" -w '%{http_code}' \
      -H 'Content-Type: application/json' \
      -d "$payload" \
      "$API_BASE/api/agent/pairing/exchange"
  )" || curl_status=$?
  if [[ "$curl_status" -ne 0 ]]; then
    rm -f "$response_file"
    fail "falha de rede ao parear agente. Verifique a internet do host e tente novamente."
  fi
  if [[ ! "$http_status" =~ ^2 ]]; then
    detail="$(extract_error_detail "$response_file" || true)"
    rm -f "$response_file"
    if [[ -n "$detail" ]]; then
      fail "falha ao parear agente (HTTP $http_status): $detail"
    fi
    fail "falha ao parear agente (HTTP $http_status). Gere um novo comando ou remova o agente antigo desta impressora no Printora."
  fi
  python3 - "$response_file" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text())
credential = payload.get("credential")
if not credential:
    raise SystemExit("resposta sem credential")
print(credential)
PY
  rm -f "$response_file"
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
    "job_journal_file": state_dir + "/job-journal.json",
    "agent_binary_path": "/usr/local/bin/printora-agent",
    "agent_service_name": "printora-agent",
    "allow_service_restart": True,
}, indent=2))
PY
  chmod 0600 "$CONFIG_DIR/config.json"
}

install_service() {
  if [[ "$SERVICE_USER" != "root" ]] && ! id "$SERVICE_USER" >/dev/null 2>&1; then
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
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE
  systemctl daemon-reload
  systemctl enable --now "$SERVICE_NAME"
}

notify_install_success() {
  local credential="$1"
  local platform payload
  platform="linux/$(uname -m)"
  payload="$(python3 - "$AGENT_VERSION" "$platform" <<'PY'
import json
import sys

print(json.dumps({
    "agent_version": sys.argv[1],
    "platform": sys.argv[2],
    "capabilities": {
        "installer": True,
        "install_success": True,
        "systemd": True,
        "websocket": True,
        "polling": True,
    },
}))
PY
)"
  if curl -fsS --max-time 10 -H "Authorization: Bearer $credential" -H 'Content-Type: application/json' -d "$payload" "$API_BASE/api/agent/heartbeat" >/dev/null; then
    log "api: instalação notificada"
  else
    log "api: aviso, instalação concluída mas heartbeat imediato falhou; o serviço tentará novamente"
  fi
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
  notify_install_success "$credential"
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

if [[ "${PRINTORA_AGENT_INSTALL_SOURCE_ONLY:-0}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

case "$MODE" in
  preflight) preflight ;;
  apply) apply_install ;;
  uninstall) uninstall ;;
  *) fail "modo inválido: $MODE" ;;
esac
