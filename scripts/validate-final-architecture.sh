#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "[final-architecture] ERROR: $*" >&2
  exit 1
}

manifest="docs/architecture/FINAL_ARCHITECTURE_MANIFEST.md"
[[ -s "$manifest" ]] || fail "manifesto final ausente"

obsolete_files=(
  backend/app/modules/platform/transition_outbox.py
  backend/sql/073_postgresql_transition_outbox.sql
  backend/sql/postgresql/002_transition_replication_state.sql
  scripts/cloud/backup-sqlite.sh
  scripts/cloud/restore-backup-test.sh
  scripts/cloud/create-sqlite-transition-snapshot.py
  scripts/cloud/import-sqlite-postgresql.py
  scripts/cloud/replicate-sqlite-outbox.py
  scripts/cloud/reconcile-sqlite-postgresql.py
  scripts/cloud/prepare-postgresql-canary.sh
  scripts/cloud/cutover-postgresql.sh
  scripts/cloud/cutover-postgresql.py
)
for file in "${obsolete_files[@]}"; do
  [[ ! -e "$file" ]] || fail "artefato aposentado presente: $file"
done

if rg -n \
  'database_transition|PRINTORA_(SQLITE_SHADOW|POSTGRESQL_SHADOW|DUAL_READ|DUAL_WRITE|TRANSITION_OUTBOX)' \
  backend/app frontend/src packaging scripts/cloud .github/workflows; then
  fail "flag, contrato ou bridge transitório encontrado"
fi

for lockfile in backend/uv.lock frontend/package-lock.json agent/go.sum; do
  [[ -s "$lockfile" ]] || fail "lockfile ausente: $lockfile"
done
grep -q 'cyclonedx-bom==7.3.0' scripts/generate-sbom.sh \
  || fail "gerador SBOM Python sem versão fixa"
grep -q 'cyclonedx-gomod/cmd/cyclonedx-gomod@v1.10.0' scripts/generate-sbom.sh \
  || fail "gerador SBOM Go sem versão fixa"

for unit in packaging/systemd/*.service packaging/systemd/*.timer packaging/systemd/*.target; do
  grep -Fq "$(basename "$unit")" "$manifest" \
    || fail "unit sem owner no manifesto: $(basename "$unit")"
done

python_bin="python3"
[[ -x backend/.venv/bin/python ]] && python_bin="backend/.venv/bin/python"
PYTHONPATH="$ROOT_DIR/backend" \
PRINTORA_RUNTIME_PROFILE=cloud \
PRINTORA_DATABASE_URL=postgresql://scan:scan@127.0.0.1:5433/printora_cloud \
"$python_bin" - <<'PY'
import sys

import app.database
import app.modules.platform.database_target

if "sqlite3" in sys.modules:
    raise SystemExit("perfil cloud carregou sqlite3")
PY

grep -q '^EnvironmentFile=/etc/printora-cloud/postgresql.env$' \
  packaging/systemd/printora-cloud@.service \
  || fail "web cloud sem ambiente PostgreSQL canônico"
grep -q '^EnvironmentFile=/etc/printora-cloud/postgresql.env$' \
  packaging/systemd/printora-cloud-worker@.service \
  || fail "worker cloud sem ambiente PostgreSQL canônico"

echo "arquitetura final e isolamento por perfil validados"
