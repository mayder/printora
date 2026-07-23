#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/run-e2e-gate.sh"
"$ROOT_DIR/scripts/run-property-fuzz-gate.sh"
"$ROOT_DIR/scripts/run-mutation-gate.sh"
