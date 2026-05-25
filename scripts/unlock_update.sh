#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

DATA_DIR="${PRINTORA_DATA_DIR:-$(mpl_data_dir)}"
DB_PATH="${DATA_DIR}/printora.db"
PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(mpl_python)"
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Python 3.11+ não encontrado." >&2
  exit 1
fi

"${PYTHON_BIN}" - "${DB_PATH}" <<'PY'
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

db_path = Path(sys.argv[1]).expanduser()
if not db_path.is_file():
    raise SystemExit(f"Banco não encontrado: {db_path}")

backup_path = db_path.with_name(
    f"{db_path.stem}.backup-before-update-unlock-{datetime.now().strftime('%Y%m%d-%H%M%S')}{db_path.suffix}"
)
shutil.copy2(db_path, backup_path)

with sqlite3.connect(db_path) as connection:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT id, target_tag, status, created_at
        FROM app_update_runs
        WHERE status = 'running'
        ORDER BY id
        """
    ).fetchall()
    print(f"Banco: {db_path}")
    print(f"Backup: {backup_path}")
    print(f"Updates travados: {len(rows)}")
    for row in rows:
        print(dict(row))

    connection.execute(
        """
        UPDATE app_update_runs
        SET status = 'failed',
            finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP),
            error_message = COALESCE(
                error_message,
                'Destravado por scripts/unlock_update.sh: update ficou órfão após reinício/interrupção.'
            )
        WHERE status = 'running'
        """
    )
    connection.execute(
        """
        UPDATE app_update_steps
        SET status = 'failed',
            finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP),
            log_excerpt = COALESCE(log_excerpt, 'Destravado junto com o update órfão.')
        WHERE status IN ('pending', 'running')
          AND run_id IN (
            SELECT id
            FROM app_update_runs
            WHERE error_message LIKE 'Destravado por scripts/unlock_update.sh:%'
          )
        """
    )
    remaining = connection.execute(
        "SELECT COUNT(*) FROM app_update_runs WHERE status = 'running'"
    ).fetchone()[0]
    print(f"Restantes em execução: {remaining}")
PY
