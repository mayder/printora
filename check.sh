#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log() { echo "[check:printora] $*"; }
fail() { echo "[check:printora] ERROR: $*" >&2; exit 1; }

run_model_validations() {
  local script
  for script in \
    scripts/validate-required-files.sh \
    scripts/validate-paths.sh \
    scripts/validate-docs.sh \
    scripts/validate-rules.sh \
    scripts/validate-no-secrets.sh \
    scripts/validate-file-size.sh \
    scripts/validate-no-runtime-pkg-names.sh \
    scripts/validate-cloud-postgresql-only.sh \
    scripts/validate-fixtures.sh \
    scripts/validate-layering.sh \
    scripts/validate-stack.sh; do
    [[ -x "$script" ]] || fail "script obrigatorio ausente ou sem execucao: $script"
    bash "$script"
  done
}

required_files=(
  "PATHS.toml"
  "ESCOPO.md"
  "QUALITY_ROADMAP.md"
  "GOVERNANCA.md"
  "DEMANDAS.md"
  "TESTES.md"
  "BUGS.md"
  "TELAS.md"
  "DECISOES.md"
  "RUNBOOK.md"
  "README.md"
  ".gitignore"
  "backend/pyproject.toml"
  "backend/app/main.py"
  "agent/go.mod"
  "agent/cmd/printora-agent/main.go"
  "frontend/package.json"
  "frontend/src/main.tsx"
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Missing or empty required file: $file" >&2
    exit 1
  fi
done

run_model_validations

log "validando inventário modular"
python3 scripts/audit_module_boundaries.py --check >/dev/null

log "validando contratos públicos versionados"
if command -v uv >/dev/null 2>&1; then
  (cd backend && uv run python ../scripts/export_api_contracts.py --check >/dev/null)
elif [[ -x backend/.venv/bin/python ]]; then
  backend/.venv/bin/python scripts/export_api_contracts.py --check >/dev/null
else
  python3 scripts/export_api_contracts.py --check >/dev/null
fi

log "python compileall"
python3 -m compileall -q backend/app backend/tests

if [[ "${RUN_PYTHON_TESTS:-0}" == "1" ]]; then
  log "pytest backend"
  if command -v uv >/dev/null 2>&1; then
    (cd backend && uv run --extra dev pytest -q)
  else
    (cd backend && python3 -m pytest -q)
  fi
else
  log "pytest backend pulado; use RUN_PYTHON_TESTS=1 ./check.sh"
fi

if [[ -d agent ]]; then
  log "go test agent"
  (cd agent && go test ./...)
fi

log "validando package.json"
python3 -m json.tool frontend/package.json >/dev/null

if [[ "${RUN_FRONTEND_CHECKS:-0}" == "1" ]]; then
  log "checks frontend"
  if [[ -d frontend/node_modules ]]; then
    (cd frontend && npm run build)
    if node -e "const s=require('./frontend/package.json').scripts||{}; process.exit(s['test:releases']?0:1)"; then
      (cd frontend && npm run test:releases)
    fi
    if node -e "const s=require('./frontend/package.json').scripts||{}; process.exit(s['test:gcode-preview']?0:1)"; then
      (cd frontend && npm run test:gcode-preview)
    fi
  else
    fail "frontend/node_modules ausente para RUN_FRONTEND_CHECKS=1"
  fi
else
  log "checks frontend pesados pulados; use RUN_FRONTEND_CHECKS=1 ./check.sh"
fi

log "OK"
