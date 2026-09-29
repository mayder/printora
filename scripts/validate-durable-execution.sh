#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required=(
  backend/app/modules/platform/durable_execution.py
  backend/app/modules/platform/event_dispatcher.py
  backend/app/modules/platform/idempotency.py
  backend/app/modules/platform/recomposable_redis.py
  backend/app/modules/platform/realtime_broker.py
  backend/app/worker.py
  backend/sql/073_durable_execution.sql
  backend/sql/postgresql/002_durable_execution.sql
  packaging/systemd/printora-cloud-worker@.service
  packaging/systemd/printora-cloud-workers.target
  packaging/systemd/redis-printora.service
)

for file in "${required[@]}"; do
  [[ -s "$file" ]] || { echo "execução durável ausente: $file" >&2; exit 1; }
done

if grep -R -nE --include='*.py' \
  'asyncio\.Queue|queue\.Queue|collections\.deque|from collections import deque' backend/app; then
  echo "fila autoritativa em memória detectada" >&2
  exit 1
fi

if grep -R -nE --include='*.py' 'agent_ws_manager\.push_job|def push_job' backend/app; then
  echo "entrega imediata autoritativa de job detectada" >&2
  exit 1
fi

grep -q 'FOR UPDATE SKIP LOCKED' backend/app/modules/platform/durable_execution.py
grep -q 'lease_token' backend/app/modules/platform/durable_execution.py
grep -q 'Idempotency-Key' backend/app/routes/worker_admin.py
grep -q '^EnvironmentFile=/etc/printora-cloud/redis.env$' packaging/systemd/printora-cloud@.service
grep -q 'apply-postgresql-schema.sh' scripts/cloud/deploy-blue-green.sh
grep -q '^unixsocket /run/redis-printora/redis.sock$' packaging/redis/printora.conf
grep -q '^appendonly no$' packaging/redis/printora.conf

if grep -nE 'execute_script\(postgresql_script' backend/app/database.py >/dev/null; then
  echo "aplicação runtime não pode executar DDL PostgreSQL" >&2
  exit 1
fi

echo "execução durável, Redis recomponível e realtime distribuído validados"
