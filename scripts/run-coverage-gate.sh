#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="${COVERAGE_ARTIFACT_DIR:-${ROOT_DIR}/.artifacts/coverage}"
NODE_BIN_DIR="${PRINTORA_NODE_BIN_DIR:-$(dirname "$(command -v node)")}"

mkdir -p "$ARTIFACT_DIR/python" "$ARTIFACT_DIR/go" "$ARTIFACT_DIR/frontend"

(
  cd "$ROOT_DIR/backend"
  uv run --extra dev pytest -q \
    --cov=app \
    --cov-report="json:${ARTIFACT_DIR}/python/coverage.json" \
    --cov-report=term \
    --cov-fail-under=79
)

(
  cd "$ROOT_DIR/agent"
  go test -coverprofile="${ARTIFACT_DIR}/go/global.out" ./...
  go tool cover -func="${ARTIFACT_DIR}/go/global.out" \
    >"${ARTIFACT_DIR}/go/global.txt"
  go test -coverprofile="${ARTIFACT_DIR}/go/critical.out" ./internal/agent
  go tool cover -func="${ARTIFACT_DIR}/go/critical.out" \
    >"${ARTIFACT_DIR}/go/critical.txt"
)

(
  cd "$ROOT_DIR/frontend"
  PATH="${NODE_BIN_DIR}:$PATH" \
    PRINTORA_COVERAGE_DIR="${ARTIFACT_DIR}/frontend" \
    npm run test:coverage
)

python3 "$ROOT_DIR/scripts/validate_coverage.py" \
  --baseline "$ROOT_DIR/quality/coverage-baseline.json" \
  --python "$ARTIFACT_DIR/python/coverage.json" \
  --go-global "$ARTIFACT_DIR/go/global.txt" \
  --go-critical "$ARTIFACT_DIR/go/critical.txt" \
  --frontend "$ARTIFACT_DIR/frontend/coverage-summary.json"
