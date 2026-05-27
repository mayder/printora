#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

INSTALL_USER="${PRINTORA_INSTALL_USER:-${USER:-pi}}"
INSTALL_HOME="${PRINTORA_INSTALL_HOME:-$(eval echo "~${INSTALL_USER}")}"
TARGET_DIR="${PRINTORA_INSTALL_DIR:-${INSTALL_HOME}/Printora}"
PUBLIC_URL="${PRINTORA_PUBLIC_URL:-http://$(hostname):8069}"
SERVICE_SRC="${ROOT_DIR}/packaging/systemd/printora.service"
SERVICE_DST="/etc/systemd/system/printora.service"
SUDOERS_DST="/etc/sudoers.d/printora-restart"
ENV_SRC="${ROOT_DIR}/packaging/env/printora.env.example"
ENV_DST="${TARGET_DIR}/.env"
MAINSAIL_NAV_SRC="${ROOT_DIR}/packaging/mainsail/navi.json"
MAINSAIL_NAV_DST="${PRINTORA_MAINSAIL_NAV_PATH:-${INSTALL_HOME}/printer_data/config/.theme/navi.json}"
UPDATE_MANAGER_SRC="${ROOT_DIR}/packaging/moonraker/update_manager_printora.conf"
UPDATE_MANAGER_DST="${PRINTORA_UPDATE_MANAGER_PATH:-${INSTALL_HOME}/printer_data/config/update_manager_printora.conf}"
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

if [[ "${APPLY}" == "true" ]]; then
  run_or_print "${TARGET_DIR}/scripts/ensure_node_runtime.sh" --apply
else
  run_or_print "${ROOT_DIR}/scripts/ensure_node_runtime.sh" --plan
fi

if [[ -f "${TARGET_DIR}/.printora-node-env" ]]; then
  # shellcheck source=/dev/null
  . "${TARGET_DIR}/.printora-node-env"
fi
NPM_BIN="${PRINTORA_NPM_BIN:-$(command -v npm 2>/dev/null || true)}"

if [[ -s "${TARGET_DIR}/frontend/dist/index.html" && "${PRINTORA_REBUILD_FRONTEND:-0}" != "1" ]]; then
  echo "Frontend dist já existe; pulando npm install/build. Use PRINTORA_REBUILD_FRONTEND=1 para rebuildar."
elif [[ -n "${NPM_BIN}" ]]; then
  run_or_print "${TARGET_DIR}/scripts/npm_frontend_install.sh" "${TARGET_DIR}/frontend" "${NPM_BIN}"
  run_or_print "${NPM_BIN}" --prefix "${TARGET_DIR}/frontend" run build
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
      -e "s#PRINTORA_DATA_DIR=/home/pi/.local/share/printora#PRINTORA_DATA_DIR=${INSTALL_HOME}/.local/share/printora#g" \
      -e "s#PRINTORA_FRONTEND_DIST_DIR=/home/pi/Printora/frontend/dist#PRINTORA_FRONTEND_DIST_DIR=${TARGET_DIR}/frontend/dist#g" \
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
  -e "s#/home/pi/Printora#${TARGET_DIR}#g" \
  "${SERVICE_SRC}" > "${SERVICE_TMP}"
run_or_print sudo cp "${SERVICE_TMP}" "${SERVICE_DST}"
rm -f "${SERVICE_TMP}"
SYSTEMCTL_BIN="$(command -v systemctl)"
SUDOERS_TMP="$(mktemp)"
cat > "${SUDOERS_TMP}" <<SUDOERS
${INSTALL_USER} ALL=NOPASSWD: ${SYSTEMCTL_BIN} restart printora.service, ${SYSTEMCTL_BIN} status printora.service
SUDOERS
if [[ "${APPLY}" == "true" ]]; then
  sudo visudo -cf "${SUDOERS_TMP}"
fi
run_or_print sudo cp "${SUDOERS_TMP}" "${SUDOERS_DST}"
run_or_print sudo chmod 440 "${SUDOERS_DST}"
rm -f "${SUDOERS_TMP}"
run_or_print sudo systemctl daemon-reload
run_or_print sudo systemctl enable printora.service
run_or_print sudo systemctl restart printora.service

run_or_print mkdir -p "$(dirname "${MAINSAIL_NAV_DST}")"
if [[ -f "${MAINSAIL_NAV_DST}" ]]; then
  run_or_print cp "${MAINSAIL_NAV_DST}" "${MAINSAIL_NAV_DST}.before-printora"
fi
MAINSAIL_NAV_TMP="$(mktemp)"
sed -e "s#http://voron.local:8069#${PUBLIC_URL}#g" "${MAINSAIL_NAV_SRC}" > "${MAINSAIL_NAV_TMP}"
run_or_print cp "${MAINSAIL_NAV_TMP}" "${MAINSAIL_NAV_DST}"
rm -f "${MAINSAIL_NAV_TMP}"

run_or_print mkdir -p "$(dirname "${UPDATE_MANAGER_DST}")"
if [[ -f "${UPDATE_MANAGER_DST}" ]]; then
  run_or_print cp "${UPDATE_MANAGER_DST}" "${UPDATE_MANAGER_DST}.before-printora"
fi
UPDATE_MANAGER_TMP="$(mktemp)"
sed -e "s#/home/pi/Printora#${TARGET_DIR}#g" "${UPDATE_MANAGER_SRC}" > "${UPDATE_MANAGER_TMP}"
run_or_print cp "${UPDATE_MANAGER_TMP}" "${UPDATE_MANAGER_DST}"
rm -f "${UPDATE_MANAGER_TMP}"

echo "Instalação preparada. Serviço configurado para iniciar no boot e reiniciado no apply."
