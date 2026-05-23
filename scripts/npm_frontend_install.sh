#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="${1:-}"
NPM_BIN="${2:-npm}"

if [[ -z "$FRONTEND_DIR" || ! -f "${FRONTEND_DIR}/package.json" ]]; then
  echo "frontend inválido: ${FRONTEND_DIR}" >&2
  exit 2
fi

if "$NPM_BIN" --prefix "$FRONTEND_DIR" install; then
  exit 0
fi

status="$?"
if [[ "${PRINTORA_NPM_CLEAN_RETRY:-1}" != "1" ]]; then
  exit "$status"
fi

echo "npm install falhou; limpando somente ${FRONTEND_DIR}/node_modules e tentando novamente." >&2
rm -rf "${FRONTEND_DIR}/node_modules"
"$NPM_BIN" cache verify >/dev/null 2>&1 || true
"$NPM_BIN" --prefix "$FRONTEND_DIR" install
