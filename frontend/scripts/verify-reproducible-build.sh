#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/printora-frontend-build.XXXXXX")"
trap 'rm -rf -- "$WORK_DIR"' EXIT

build_manifest() {
  local output_file="$1"
  (
    cd "$FRONTEND_DIR"
    npm run build >/dev/null
    find dist -type f -print0 \
      | LC_ALL=C sort -z \
      | xargs -0 shasum -a 256 \
      | sed 's#  dist/#  #' >"$output_file"
  )
}

build_manifest "$WORK_DIR/first.sha256"
build_manifest "$WORK_DIR/second.sha256"
cmp "$WORK_DIR/first.sha256" "$WORK_DIR/second.sha256"
echo "frontend reproducible build passed"
