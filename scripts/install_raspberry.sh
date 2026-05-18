#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
