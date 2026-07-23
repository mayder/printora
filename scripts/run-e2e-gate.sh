#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$(mktemp -d "${TMPDIR:-/tmp}/printora-e2e-data.XXXXXX")"
ARTIFACT_DIR="${E2E_ARTIFACT_DIR:-${ROOT_DIR}/.artifacts/e2e}"
PORT="${PRINTORA_E2E_PORT:-18069}"
DIST_DIR="${ARTIFACT_DIR}/dist"
ADMIN_PASSWORD_FILE="${DATA_DIR}/e2e-admin-password"

mkdir -p "$ARTIFACT_DIR"
(
  umask 077
  printf '%s' "synthetic-correct-horse-97" > "$ADMIN_PASSWORD_FILE"
)
(
  cd "$ROOT_DIR/frontend"
  VITE_PRINTORA_API_BASE_URL="http://127.0.0.1:${PORT}" \
    npx vite build --outDir "$DIST_DIR"
  PRINTORA_E2E_DATA_DIR="$DATA_DIR" \
    PRINTORA_E2E_ARTIFACT_DIR="$ARTIFACT_DIR" \
  PRINTORA_E2E_DIST_DIR="$DIST_DIR" \
    PRINTORA_E2E_ADMIN_PASSWORD_FILE="$ADMIN_PASSWORD_FILE" \
    PRINTORA_E2E_PORT="$PORT" \
    npm run test:e2e
)

echo "E2E passou com dados sintéticos isolados em $DATA_DIR"
