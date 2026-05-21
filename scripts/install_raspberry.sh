#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

INSTALL_USER="${MAYDER_PRINT_LAB_INSTALL_USER:-${USER:-pi}}"
INSTALL_HOME="${MAYDER_PRINT_LAB_INSTALL_HOME:-$(eval echo "~${INSTALL_USER}")}"
TARGET_DIR="${MAYDER_PRINT_LAB_INSTALL_DIR:-${INSTALL_HOME}/MayderPrintLab}"
PUBLIC_URL="${MAYDER_PRINT_LAB_PUBLIC_URL:-http://$(hostname):8085}"
SERVICE_SRC="${ROOT_DIR}/packaging/systemd/mayderprintlab.service"
SERVICE_DST="/etc/systemd/system/mayderprintlab.service"
ENV_SRC="${ROOT_DIR}/packaging/env/mayderprintlab.env.example"
ENV_DST="${TARGET_DIR}/.env"
MAINSAIL_NAV_SRC="${ROOT_DIR}/packaging/mainsail/navi.json"
MAINSAIL_NAV_DST="${MAYDER_PRINT_LAB_MAINSAIL_NAV_PATH:-${INSTALL_HOME}/printer_data/config/.theme/navi.json}"
UPDATE_MANAGER_SRC="${ROOT_DIR}/packaging/moonraker/update_manager_mayderprintlab.conf"
UPDATE_MANAGER_DST="${MAYDER_PRINT_LAB_UPDATE_MANAGER_PATH:-${INSTALL_HOME}/printer_data/config/update_manager_mayderprintlab.conf}"
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

if command -v npm >/dev/null 2>&1; then
  run_or_print npm --prefix "${TARGET_DIR}/frontend" install
  run_or_print npm --prefix "${TARGET_DIR}/frontend" run build
elif [[ -f "${TARGET_DIR}/frontend/dist/index.html" ]]; then
  echo "npm não encontrado; usando frontend/dist já buildado em ${TARGET_DIR}/frontend/dist."
else
  echo "npm não encontrado e frontend/dist ausente. Gere o build antes de instalar neste host." >&2
  exit 1
fi

if [[ ! -f "${ENV_DST}" ]]; then
  run_or_print cp "${ENV_SRC}" "${ENV_DST}"
  if [[ "${APPLY}" == "true" ]]; then
    sed -i \
      -e "s#MAYDER_PRINT_LAB_DATA_DIR=/home/pi/.local/share/mayderprintlab#MAYDER_PRINT_LAB_DATA_DIR=${INSTALL_HOME}/.local/share/mayderprintlab#g" \
      -e "s#MAYDER_PRINT_LAB_FRONTEND_DIST_DIR=/home/pi/MayderPrintLab/frontend/dist#MAYDER_PRINT_LAB_FRONTEND_DIST_DIR=${TARGET_DIR}/frontend/dist#g" \
      "${ENV_DST}"
  else
    echo "DRY-RUN: sed -i caminhos de ${ENV_DST} para ${INSTALL_HOME}"
  fi
else
  echo "Mantendo .env existente: ${ENV_DST}"
fi

SERVICE_TMP="$(mktemp)"
sed \
  -e "s#User=pi#User=${INSTALL_USER}#g" \
  -e "s#/home/pi/MayderPrintLab#${TARGET_DIR}#g" \
  "${SERVICE_SRC}" > "${SERVICE_TMP}"
run_or_print sudo cp "${SERVICE_TMP}" "${SERVICE_DST}"
rm -f "${SERVICE_TMP}"
run_or_print sudo systemctl daemon-reload
run_or_print sudo systemctl enable mayderprintlab.service

run_or_print mkdir -p "$(dirname "${MAINSAIL_NAV_DST}")"
if [[ -f "${MAINSAIL_NAV_DST}" ]]; then
  run_or_print cp "${MAINSAIL_NAV_DST}" "${MAINSAIL_NAV_DST}.before-mayderprintlab"
fi
MAINSAIL_NAV_TMP="$(mktemp)"
sed -e "s#http://voron.local:8085#${PUBLIC_URL}#g" "${MAINSAIL_NAV_SRC}" > "${MAINSAIL_NAV_TMP}"
run_or_print cp "${MAINSAIL_NAV_TMP}" "${MAINSAIL_NAV_DST}"
rm -f "${MAINSAIL_NAV_TMP}"

run_or_print mkdir -p "$(dirname "${UPDATE_MANAGER_DST}")"
if [[ -f "${UPDATE_MANAGER_DST}" ]]; then
  run_or_print cp "${UPDATE_MANAGER_DST}" "${UPDATE_MANAGER_DST}.before-mayderprintlab"
fi
UPDATE_MANAGER_TMP="$(mktemp)"
sed -e "s#/home/pi/MayderPrintLab#${TARGET_DIR}#g" "${UPDATE_MANAGER_SRC}" > "${UPDATE_MANAGER_TMP}"
run_or_print cp "${UPDATE_MANAGER_TMP}" "${UPDATE_MANAGER_DST}"
rm -f "${UPDATE_MANAGER_TMP}"

echo "Instalação preparada. Iniciar manualmente depois de revisar .env:"
echo "sudo systemctl start mayderprintlab.service"
