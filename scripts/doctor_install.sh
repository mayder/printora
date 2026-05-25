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

section() {
  printf '\n== %s ==\n' "$1"
}

print_command() {
  printf '$ %s\n' "$*"
  "$@" 2>&1 || true
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
for candidate in python3 python3.14 python3.13 python3.12 python3.11 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    printf '%s -> ' "$candidate"
    "$candidate" --version 2>&1 || true
  fi
done
if [[ -x "${ROOT_DIR}/backend/.venv/bin/python" ]]; then
  printf 'backend_venv -> '
  "${ROOT_DIR}/backend/.venv/bin/python" --version 2>&1 || true
else
  echo "backend_venv=missing"
fi

section "Node"
if [[ -f "${ROOT_DIR}/.printora-node-env" ]]; then
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.printora-node-env"
fi
print_command node --version
print_command npm --version

section "Projeto"
test -f "${ROOT_DIR}/backend/pyproject.toml" && echo "backend pyproject ok" || echo "backend pyproject ausente"
test -s "${ROOT_DIR}/frontend/dist/index.html" && echo "frontend dist ok" || echo "frontend dist ausente"
test -f "${DATA_DIR}/printora.db" && echo "banco ok: ${DATA_DIR}/printora.db" || echo "banco ausente"

section "Porta e saúde"
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN 2>&1 || true
fi
curl -fsS --max-time 5 "${HEALTH_URL}" 2>&1 || true

section "Serviço"
case "$(mpl_os)" in
  macos)
    print_command launchctl print "gui/$(id -u)/com.printora.app"
    ;;
  linux)
    if mpl_has_systemd; then
      print_command systemctl status printora.service --no-pager
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
