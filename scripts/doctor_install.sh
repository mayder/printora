#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

PORT="${PRINTORA_PORT:-8069}"
HOST="${PRINTORA_HOST:-127.0.0.1}"
DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
HEALTH_HOST="${HOST}"
if [[ "${HEALTH_HOST}" == "0.0.0.0" ]]; then
  HEALTH_HOST="127.0.0.1"
fi
HEALTH_URL="http://${HEALTH_HOST}:${PORT}/health"

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  C_RESET="$(tput sgr0)"
  C_OK="$(tput setaf 2)"
  C_WARN="$(tput setaf 3)"
  C_FAIL="$(tput setaf 1)"
else
  C_RESET=""
  C_OK=""
  C_WARN=""
  C_FAIL=""
fi

section() {
  printf '\n== %s ==\n' "$1"
}

ok() { printf '%sOK:%s %s\n' "${C_OK}" "${C_RESET}" "$*"; }
warn() { printf '%sATENÇÃO:%s %s\n' "${C_WARN}" "${C_RESET}" "$*"; }
fail() { printf '%sERRO:%s %s\n' "${C_FAIL}" "${C_RESET}" "$*"; }

print_command() {
  printf '$ %s\n' "$*"
  "$@" 2>&1 || true
}

suggest_installer() {
  case "$(mpl_os)" in
    macos) echo "./scripts/install-macos.sh" ;;
    linux)
      if [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]]; then
        echo "./scripts/install-android-termux.sh"
      else
        echo "./scripts/install-linux.sh"
      fi
      ;;
    windows) echo ".\\scripts\\install-windows.ps1" ;;
    *) echo "./scripts/install_printora.sh --apply --yes" ;;
  esac
}

section "Ambiente"
echo "root_dir=${ROOT_DIR}"
echo "data_dir=${DATA_DIR}"
echo "host=${HOST}"
echo "port=${PORT}"
echo "health_url=${HEALTH_URL}"
echo "platform=$(mpl_os)"

section "Python"
PYTHON_BIN="$(mpl_python)"
echo "selected_python=${PYTHON_BIN:-missing}"
if [[ -n "${PYTHON_BIN}" ]]; then
  ok "Python compatível encontrado: $("${PYTHON_BIN}" --version 2>&1)"
else
  fail "Python 3.11+ não encontrado."
  echo "Ação sugerida: $(suggest_installer)"
fi
for candidate in python3 python3.14 python3.13 python3.12 python3.11 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    printf '%s -> ' "$candidate"
    "$candidate" --version 2>&1 || true
  fi
done
if [[ -x "${ROOT_DIR}/backend/.venv/bin/python" ]]; then
  printf 'backend_venv -> '
  "${ROOT_DIR}/backend/.venv/bin/python" --version 2>&1 || true
  if ! "${ROOT_DIR}/backend/.venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    fail "A venv do backend foi criada com Python incompatível."
    echo "Ação sugerida: rm -rf backend/.venv && $(suggest_installer)"
  else
    ok "venv do backend usa Python compatível."
  fi
else
  warn "backend_venv=missing"
  echo "Ação sugerida: $(suggest_installer)"
fi

section "Node"
if [[ -f "${ROOT_DIR}/.printora-node-env" ]]; then
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.printora-node-env"
fi
print_command node --version
print_command npm --version
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  ok "Node/npm encontrados."
else
  fail "Node/npm ausente."
  echo "Ação sugerida: $(suggest_installer)"
fi

section "Projeto"
test -f "${ROOT_DIR}/backend/pyproject.toml" && ok "backend pyproject ok" || fail "backend pyproject ausente"
if test -s "${ROOT_DIR}/frontend/dist/index.html"; then
  ok "frontend dist ok"
else
  warn "frontend dist ausente"
  echo "Ação sugerida: PRINTORA_REBUILD_FRONTEND=1 $(suggest_installer)"
fi
if test -f "${DATA_DIR}/printora.db"; then
  ok "banco ok: ${DATA_DIR}/printora.db"
else
  warn "banco ausente"
  echo "Ação sugerida: inicie o Printora uma vez para criar o banco local."
fi

section "Porta e saúde"
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN 2>&1 || true
fi
HEALTH_OUTPUT="$(mktemp)"
if curl -fsS --max-time 5 "${HEALTH_URL}" >"${HEALTH_OUTPUT}" 2>&1; then
  ok "Printora respondeu em ${HEALTH_URL}: $(cat "${HEALTH_OUTPUT}")"
else
  fail "Printora não respondeu em ${HEALTH_URL}."
  cat "${HEALTH_OUTPUT}" || true
  echo "Ação sugerida: $(suggest_installer)"
fi
rm -f "${HEALTH_OUTPUT}"

section "Serviço"
case "$(mpl_os)" in
  macos)
    print_command launchctl print "gui/$(id -u)/com.printora.app"
    ;;
  linux)
    if mpl_has_systemd; then
      print_command systemctl status printora.service --no-pager
      if [[ -f /etc/sudoers.d/printora-restart ]]; then
        ok "sudoers printora-restart configurado"
      else
        warn "sudoers printora-restart ausente; update automático pode não reiniciar printora.service sem senha"
        echo "Ação sugerida: rode scripts/install_printora_autostart.sh --apply --yes ou scripts/install_raspberry.sh --apply."
      fi
    fi
    ;;
esac

section "Logs"
for log_file in \
  "${DATA_DIR}/logs/app.log" \
  "${DATA_DIR}/logs/launchd.log" \
  "${DATA_DIR}/logs/launchd.err.log" \
  "${DATA_DIR}/logs/boot.log"; do
  if [[ -f "${log_file}" ]]; then
    echo "--- ${log_file}"
    tail -n 80 "${log_file}" || true
  fi
done
