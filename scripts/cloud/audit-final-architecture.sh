#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"
require_root

release_dir="$(readlink -f "$PRINTORA_BASE_PATH/current")"
[[ -d "$release_dir/backend" ]] || fail "release corrente ausente"
active="$(active_slot)"
replica_dir="$(readlink -f "$PRINTORA_BASE_PATH/slots/replica")"
[[ "$release_dir" == "$replica_dir" ]] || fail "réplica diverge da release ativa"

for port in 8069 8071; do
  curl --max-time 2 -fsS "http://127.0.0.1:$port/ready" >/dev/null
done
for unit in \
  "printora-cloud@$active.service" \
  printora-cloud@replica.service \
  printora-cloud-workers.target \
  printora-cloud-intelligence.service \
  printora-cloud-backup.timer \
  printora-cloud-wal-sync.timer \
  printora-cloud-restore-test.timer \
  printora-cloud-recovery-monitor.timer \
  postgresql@16-printora.service \
  redis-printora.service \
  minio-printora.service; do
  systemctl is-active --quiet "$unit" || fail "unit inativa: $unit"
done

/usr/local/libexec/printora-cloud/recovery-readiness.py >/dev/null \
  || fail "prontidão de recuperação divergente"

obsolete=(
  transition_outbox.py
  073_postgresql_transition_outbox.sql
  002_transition_replication_state.sql
  backup-sqlite.sh
  restore-backup-test.sh
  create-sqlite-transition-snapshot.py
  import-sqlite-postgresql.py
  replicate-sqlite-outbox.py
  reconcile-sqlite-postgresql.py
  prepare-postgresql-canary.sh
  cutover-postgresql.sh
  cutover-postgresql.py
)
for name in "${obsolete[@]}"; do
  if find "$release_dir" /usr/local/libexec/printora-cloud -type f -name "$name" -print -quit \
    | grep -q .; then
    fail "artefato aposentado presente: $name"
  fi
done

set -a
source "$PRINTORA_BASE_PATH/shared/printora-cloud.env"
source /etc/printora-cloud/postgresql.env
source /etc/printora-cloud/object-storage.env
source /etc/printora-cloud/redis.env
set +a
export PRINTORA_RUNTIME_PROFILE=cloud
PYTHONPATH="$release_dir/backend" "$release_dir/venv/bin/python" - <<'PY'
import sys

import app.database
import app.object_storage

if "sqlite3" in sys.modules:
    raise SystemExit("perfil cloud carregou sqlite3")
PY

database_state="$(runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc "
SELECT
  (SELECT count(*) FROM pg_tables WHERE schemaname='public') || ':' ||
  (SELECT count(*) FROM schema_versions) || ':' ||
  (SELECT count(*) FROM pg_index WHERE NOT indisvalid) || ':' ||
  (SELECT count(*) FROM pg_constraint WHERE NOT convalidated) || ':' ||
  has_table_privilege('printora_analytics','analytics_events','UPDATE')::int || ':' ||
  has_table_privilege('printora_analytics','auth_users','SELECT')::int || ':' ||
  has_table_privilege('printora_analytics','auth_users','UPDATE')::int
")"
IFS=: read -r tables revisions invalid_indexes invalid_constraints analytics_write oltp_read oltp_write \
  <<< "$database_state"
[[ "$invalid_indexes" == "0" && "$invalid_constraints" == "0" ]] \
  || fail "índice ou constraint inválida"
[[ "$analytics_write:$oltp_read:$oltp_write" == "1:0:0" ]] \
  || fail "role analítica divergente"

queue_state="$(runuser -u postgres -- psql -p 5433 -d printora_cloud -X -Atqc "
SELECT
  (SELECT count(*) FROM durable_jobs WHERE status IN ('leased','running')) || ':' ||
  (SELECT count(*) FROM outbox_events WHERE status='processing') || ':' ||
  (SELECT count(*) FROM cloud_objects) || ':' ||
  (SELECT count(*) FROM cloud_object_references)
")"

echo "status=passed"
echo "release=$(basename "$release_dir")"
echo "active_slot=$active"
echo "web_replicas=2"
echo "cloud_sqlite_loaded=false"
echo "tables=$tables"
echo "schema_versions=$revisions"
echo "invalid_indexes=$invalid_indexes"
echo "invalid_constraints=$invalid_constraints"
echo "analytics_role=$analytics_write:$oltp_read:$oltp_write"
echo "jobs_outbox_objects_references=$queue_state"
