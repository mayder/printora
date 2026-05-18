#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

TARGET_DIR="${MAYDER_PRINT_LAB_INSTALL_DIR:-/home/pi/MayderPrintLab}"
SERVICE_SRC="${ROOT_DIR}/packaging/systemd/mayderprintlab.service"
SERVICE_DST="/etc/systemd/system/mayderprintlab.service"
ENV_SRC="${ROOT_DIR}/packaging/env/mayderprintlab.env.example"
ENV_DST="${TARGET_DIR}/.env"
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

if [[ "${APPLY}" != "true" ]]; then
  echo "Modo dry-run. Reexecute com --apply para instalar."
fi

if [[ "$(mpl_os)" != "linux" ]]; then
  echo "Este instalador é para Linux/Raspberry/Manta com systemd." >&2
  echo "Para macOS/Windows/dev, use scripts/bootstrap_dev.sh." >&2
  exit 1
fi

if ! mpl_has_systemd; then
  echo "systemd não detectado. Use scripts/bootstrap_dev.sh ou Docker." >&2
  exit 1
fi

mpl_require_command rsync
mpl_require_command npm

run_or_print mkdir -p "${TARGET_DIR}"

if [[ "${ROOT_DIR}" != "${TARGET_DIR}" ]]; then
  run_or_print rsync -a --delete \
    --exclude ".git" \
    --exclude "backend/.venv" \
    --exclude "frontend/node_modules" \
    "${ROOT_DIR}/" "${TARGET_DIR}/"
fi

run_or_print python3 -m venv "${TARGET_DIR}/backend/.venv"
run_or_print "${TARGET_DIR}/backend/.venv/bin/pip" install -e "${TARGET_DIR}/backend"
run_or_print npm --prefix "${TARGET_DIR}/frontend" install
run_or_print npm --prefix "${TARGET_DIR}/frontend" run build

if [[ ! -f "${ENV_DST}" ]]; then
  run_or_print cp "${ENV_SRC}" "${ENV_DST}"
else
  echo "Mantendo .env existente: ${ENV_DST}"
fi

run_or_print sudo cp "${SERVICE_SRC}" "${SERVICE_DST}"
run_or_print sudo systemctl daemon-reload
run_or_print sudo systemctl enable mayderprintlab.service

echo "Instalação preparada. Iniciar manualmente depois de revisar .env:"
echo "sudo systemctl start mayderprintlab.service"
