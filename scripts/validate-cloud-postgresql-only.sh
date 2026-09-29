#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

runtime_files=(
  packaging/systemd/printora-cloud@.service
  packaging/systemd/printora-cloud-backup.service
  packaging/sudoers/printora-cloud-deploy
  scripts/cloud/bootstrap-blue-green.sh
  scripts/cloud/deploy-blue-green.sh
  scripts/cloud/preflight.sh
  scripts/cloud/rollback-blue-green.sh
)
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

if rg -ni 'sqlite|transition_outbox|postgresql-(canary|cutover)' "${runtime_files[@]}"; then
  echo "runtime/deploy cloud ainda referencia mecanismo aposentado" >&2
  exit 1
fi

for file in "${obsolete_files[@]}"; do
  if [[ -e "$file" ]]; then
    echo "artefato transitório ainda existe: $file" >&2
    exit 1
  fi
done

grep -q '^EnvironmentFile=/etc/printora-cloud/postgresql.env$' \
  packaging/systemd/printora-cloud@.service
grep -q 'postgresql_runtime' scripts/cloud/preflight.sh
echo "runtime cloud PostgreSQL-only validado"
