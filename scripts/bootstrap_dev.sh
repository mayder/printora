#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

PYTHON_BIN="$(mpl_python)"
DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
APPLY="false"

if [[ "${1:-}" == "--apply" ]]; then
  APPLY="true"
fi

run_or_print() {
  if [[ "${APPLY}" == "true" ]]; then
    "$@"
  else
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
  fi
}

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Python não encontrado." >&2
  exit 1
fi

if [[ "${APPLY}" == "true" ]]; then
  "${ROOT_DIR}/scripts/ensure_node_runtime.sh" --apply
else
  "${ROOT_DIR}/scripts/ensure_node_runtime.sh" --plan
fi

if [[ -f "${ROOT_DIR}/.printora-node-env" ]]; then
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.printora-node-env"
fi

NPM_BIN="${PRINTORA_NPM_BIN:-$(command -v npm 2>/dev/null || true)}"
if [[ -z "${NPM_BIN}" ]]; then
  echo "npm não encontrado." >&2
  exit 1
fi

echo "Sistema detectado: $(mpl_os)"
echo "Data dir: ${DATA_DIR}"
if [[ "${APPLY}" != "true" ]]; then
  echo "Modo dry-run. Reexecute com --apply para preparar o ambiente local."
fi

run_or_print mkdir -p "${DATA_DIR}"
run_or_print "${PYTHON_BIN}" -m venv "${ROOT_DIR}/backend/.venv"
run_or_print "${ROOT_DIR}/backend/.venv/bin/pip" install -e "${ROOT_DIR}/backend[dev]"
run_or_print "${NPM_BIN}" --prefix "${ROOT_DIR}/frontend" install
run_or_print "${NPM_BIN}" --prefix "${ROOT_DIR}/frontend" run build

echo "Ambiente local preparado."
echo "Backend: ${ROOT_DIR}/scripts/dev_backend.sh"
echo "Frontend: ${ROOT_DIR}/scripts/dev_frontend.sh"
