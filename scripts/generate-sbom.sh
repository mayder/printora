#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$ROOT_DIR/.artifacts/sbom}"

case "$OUTPUT_DIR" in
  /*) ;;
  *) OUTPUT_DIR="$ROOT_DIR/$OUTPUT_DIR" ;;
esac

mkdir -p "$OUTPUT_DIR"

PYTHON_REQUIREMENTS="$OUTPUT_DIR/backend-requirements.txt"
PYTHON_SBOM="$OUTPUT_DIR/backend.cdx.json"
FRONTEND_SBOM="$OUTPUT_DIR/frontend.cdx.json"
AGENT_SBOM="$OUTPUT_DIR/agent.cdx.json"

(
  cd "$ROOT_DIR/backend"
  uv export \
    --frozen \
    --no-dev \
    --format requirements-txt \
    --no-emit-project \
    --output-file "$PYTHON_REQUIREMENTS" >/dev/null
  uvx --from cyclonedx-bom==7.3.0 cyclonedx-py requirements \
    "$PYTHON_REQUIREMENTS" \
    --pyproject pyproject.toml \
    --mc-type application \
    --spec-version 1.6 \
    --output-reproducible \
    --output-format JSON \
    --output-file "$PYTHON_SBOM"
)

(
  cd "$ROOT_DIR/frontend"
  npm sbom \
    --package-lock-only \
    --omit=dev \
    --sbom-format cyclonedx \
    --sbom-type application > "$FRONTEND_SBOM"
)

python3 - "$FRONTEND_SBOM" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as stream:
    payload = json.load(stream)
payload.pop("serialNumber", None)
payload.get("metadata", {}).pop("timestamp", None)
with open(path, "w", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    stream.write("\n")
PY

(
  cd "$ROOT_DIR/agent"
  go run github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@v1.10.0 \
    mod \
    -json \
    -noserial \
    -notimestamp \
    -output-version 1.6 \
    -output "$AGENT_SBOM" \
    .
)

python3 - "$PYTHON_SBOM" "$FRONTEND_SBOM" "$AGENT_SBOM" <<'PY'
import json
import sys

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("bomFormat") != "CycloneDX":
        raise SystemExit(f"SBOM inválido: {path}")
    if not payload.get("components"):
        raise SystemExit(f"SBOM sem componentes: {path}")
PY

(
  cd "$OUTPUT_DIR"
  shasum -a 256 \
    backend-requirements.txt \
    backend.cdx.json \
    frontend.cdx.json \
    agent.cdx.json > SHA256SUMS
)

printf 'SBOM CycloneDX gerado em %s\n' "$OUTPUT_DIR"
