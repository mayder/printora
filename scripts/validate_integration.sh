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

require_file "packaging/systemd/printora.service"
require_file "packaging/env/printora.env.example"
require_file "packaging/mainsail/navi.json"
require_file "packaging/moonraker/update_manager_printora.conf"
require_file "scripts/install_raspberry.sh"
require_file "docs/INSTALL_RASPBERRY.md"

require_contains "packaging/systemd/printora.service" "ExecStart=/home/pi/Printora/backend/.venv/bin/python -m uvicorn"
require_contains "packaging/env/printora.env.example" "PRINTORA_FIRMWARE_BUILD_MODE=disabled"
require_contains "packaging/mainsail/navi.json" "Printora"
require_contains "packaging/moonraker/update_manager_printora.conf" "[update_manager printora]"
require_contains "scripts/install_raspberry.sh" "Modo dry-run"
require_contains "scripts/install_raspberry.sh" "before-printora"
require_contains "docs/INSTALL_RASPBERRY.md" "Rollback"

echo "Integração Mainsail/Moonraker/systemd validada em modo offline."
