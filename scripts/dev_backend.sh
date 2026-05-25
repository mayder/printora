#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

export PRINTORA_DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
cd "${ROOT_DIR}/backend"
exec "${ROOT_DIR}/backend/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8069 --reload
