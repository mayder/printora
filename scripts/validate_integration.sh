#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_file() {
  local path="$1"
  if [[ ! -f "${ROOT_DIR}/${path}" ]]; then
    echo "Arquivo obrigatório ausente: ${path}" >&2
    exit 1
  fi
}

require_contains() {
  local path="$1"
  local expected="$2"
  if ! grep -Fq "${expected}" "${ROOT_DIR}/${path}"; then
    echo "Conteúdo esperado ausente em ${path}: ${expected}" >&2
    exit 1
  fi
}

require_file "packaging/systemd/mayderprintlab.service"
require_file "packaging/env/mayderprintlab.env.example"
require_file "packaging/mainsail/navi.json"
require_file "packaging/moonraker/update_manager_mayderprintlab.conf"
require_file "scripts/install_raspberry.sh"
require_file "docs/INSTALL_RASPBERRY.md"

require_contains "packaging/systemd/mayderprintlab.service" "ExecStart=/home/pi/MayderPrintLab/backend/.venv/bin/python -m uvicorn"
require_contains "packaging/env/mayderprintlab.env.example" "MAYDER_PRINT_LAB_FIRMWARE_BUILD_MODE=disabled"
require_contains "packaging/mainsail/navi.json" "MayderPrintLab"
require_contains "packaging/moonraker/update_manager_mayderprintlab.conf" "[update_manager mayderprintlab]"
require_contains "scripts/install_raspberry.sh" "Modo dry-run"
require_contains "scripts/install_raspberry.sh" "before-mayderprintlab"
require_contains "docs/INSTALL_RASPBERRY.md" "Rollback"

echo "Integração Mainsail/Moonraker/systemd validada em modo offline."
