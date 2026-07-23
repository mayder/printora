#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED="${PRINTORA_FUZZ_SEED:-970099}"

cd "$ROOT_DIR/backend"
HYPOTHESIS_PROFILE=ci uv run --extra dev pytest -q tests/test_property_fuzz.py
HYPOTHESIS_PROFILE=fuzz uv run --extra dev pytest -q \
  --hypothesis-seed="$SEED" \
  tests/test_property_fuzz.py

echo "Property/fuzz passou com corpus versionado e seed $SEED"
