#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

HOST="${PRINTORA_HOST:-127.0.0.1}"
PORT="${PRINTORA_PORT:-8085}"
URL="http://${HOST}:${PORT}"
DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
LOG_DIR="${DATA_DIR}/logs"
PID_FILE="${DATA_DIR}/printora.pid"
LOG_FILE="${LOG_DIR}/app.log"
OPEN_BROWSER="true"
STOP_ONLY="false"
STATUS_ONLY="false"
FOREGROUND="false"

usage() {
  cat <<'USAGE'
Uso:
  scripts/run_app.sh            # prepara se precisar, inicia e abre o app
  scripts/run_app.sh --no-open  # inicia sem abrir navegador
  scripts/run_app.sh --foreground # mantém o servidor no terminal atual
  scripts/run_app.sh --status   # mostra status local
  scripts/run_app.sh --stop     # para o processo iniciado por este runner

Variáveis úteis:
  PRINTORA_PORT=8085
  PRINTORA_MOONRAKER_URL=http://voron.local:7125
USAGE
}

for arg in "$@"; do
  case "${arg}" in
    --no-open) OPEN_BROWSER="false" ;;
    --foreground) FOREGROUND="true" ;;
    --status) STATUS_ONLY="true" ;;
    --stop) STOP_ONLY="true" ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento inválido: ${arg}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

http_ok() {
  curl -fsS "${URL}/health" >/dev/null 2>&1
}

pid_alive() {
  [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" >/dev/null 2>&1
}

open_url() {
  case "$(mpl_os)" in
    macos) open "${URL}" ;;
    linux)
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}" >/dev/null 2>&1 || true
      fi
      ;;
  esac
}

stop_app() {
  if pid_alive; then
    kill "$(cat "${PID_FILE}")"
    rm -f "${PID_FILE}"
    echo "Printora parada."
    return
  fi
  rm -f "${PID_FILE}"
  echo "Printora não estava rodando por este runner."
}

if [[ "${STOP_ONLY}" == "true" ]]; then
  stop_app
  exit 0
fi

if [[ "${STATUS_ONLY}" == "true" ]]; then
  if http_ok; then
    echo "Printora online em ${URL}"
  else
    echo "Printora offline em ${URL}"
  fi
  exit 0
fi

mkdir -p "${LOG_DIR}"

if http_ok; then
  echo "Printora já está online em ${URL}"
  [[ "${OPEN_BROWSER}" == "true" ]] && open_url
  exit 0
fi

PYTHON_BIN="$(mpl_python)"
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Python não encontrado." >&2
  exit 1
fi
mpl_require_command curl

if [[ -f "${ROOT_DIR}/.printora-node-env" ]]; then
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.printora-node-env"
fi
NPM_BIN="${PRINTORA_NPM_BIN:-$(command -v npm 2>/dev/null || true)}"
if [[ -z "${NPM_BIN}" ]]; then
  echo "npm não encontrado. Rode scripts/bootstrap_dev.sh --apply para preparar Node local do Printora." >&2
  exit 1
fi

if [[ ! -x "${ROOT_DIR}/backend/.venv/bin/python" ]]; then
  "${PYTHON_BIN}" -m venv "${ROOT_DIR}/backend/.venv"
  "${ROOT_DIR}/backend/.venv/bin/pip" install -e "${ROOT_DIR}/backend[dev]"
fi

if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  "${ROOT_DIR}/scripts/npm_frontend_install.sh" "${ROOT_DIR}/frontend" "${NPM_BIN}"
fi

if [[ ! -s "${ROOT_DIR}/frontend/dist/index.html" ]]; then
  "${NPM_BIN}" --prefix "${ROOT_DIR}/frontend" run build
fi

export PRINTORA_DATA_DIR="${DATA_DIR}"
export PRINTORA_MOONRAKER_URL="${PRINTORA_MOONRAKER_URL:-http://voron.local:7125}"

if [[ "${FOREGROUND}" == "true" ]]; then
  echo "$$" >"${PID_FILE}"
  echo "Printora iniciando em ${URL}"
  echo "Log: terminal atual"
  if [[ "${OPEN_BROWSER}" == "true" ]]; then
    (sleep 2 && open_url) >/dev/null 2>&1 &
  fi
  cd "${ROOT_DIR}/backend"
  exec "${ROOT_DIR}/backend/.venv/bin/python" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
fi

nohup bash -c '
  set -euo pipefail
  cd "$1"
  exec "$2" -m uvicorn app.main:app --host "$3" --port "$4"
' bash "${ROOT_DIR}/backend" "${ROOT_DIR}/backend/.venv/bin/python" "${HOST}" "${PORT}" >"${LOG_FILE}" 2>&1 &

echo "$!" >"${PID_FILE}"

for _ in $(seq 1 30); do
  if http_ok && pid_alive; then
    echo "Printora online em ${URL}"
    echo "Log: ${LOG_FILE}"
    [[ "${OPEN_BROWSER}" == "true" ]] && open_url
    exit 0
  fi
  if ! pid_alive; then
    break
  fi
  sleep 1
done

echo "Printora não subiu em ${URL}." >&2
echo "Log: ${LOG_FILE}" >&2
exit 1
