#!/usr/bin/env bash
set -euo pipefail

MODE=""
TARGET_TAG=""
RUN_ID=""
PREVIOUS_PATH=""
DB_BACKUP_PATH=""
UPDATE_RUN_ID="${PRINTORA_UPDATE_RUN_ID:-}"

ROOT_DIR="${ROOT_DIR:-${HOME}/Printora}"
DATA_DIR="${PRINTORA_DATA_DIR:-${HOME}/.local/share/printora}"
DB_PATH="${PRINTORA_DB_PATH:-${DATA_DIR}/printora.db}"
BACKUP_DIR="${PRINTORA_BACKUP_DIR:-${DATA_DIR}/backups}"
NEXT_DIR="${PRINTORA_NEXT_DIR:-${HOME}/Printora.next}"
HTTP_PORT="${HTTP_PORT:-${PRINTORA_PORT:-8069}}"
PUBLIC_PORT="${PUBLIC_PORT:-${HTTP_PORT}}"
HOST_NAME="${HOST_NAME:-printora}"
HEALTH_URL="${PRINTORA_HEALTH_URL:-http://127.0.0.1:${HTTP_PORT}/health}"
UPDATE_REMOTE_URL="${PRINTORA_UPDATE_REMOTE_URL:-}"

usage() {
  cat <<'USAGE'
Uso:
  scripts/android_update_printora.sh --plan --tag vX.Y.Z
  scripts/android_update_printora.sh --apply --tag vX.Y.Z
  scripts/android_update_printora.sh --rollback --previous-path /path/anterior [--db-backup /path/backup.db]
  scripts/android_update_printora.sh --rollback --run-id ID --previous-path /path/anterior [--db-backup /path/backup.db]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan" ;;
    --apply) MODE="apply" ;;
    --rollback) MODE="rollback" ;;
    --tag)
      shift
      TARGET_TAG="${1:-}"
      ;;
    --run-id)
      shift
      RUN_ID="${1:-}"
      UPDATE_RUN_ID="${RUN_ID}"
      ;;
    --previous-path)
      shift
      PREVIOUS_PATH="${1:-}"
      ;;
    --db-backup)
      shift
      DB_BACKUP_PATH="${1:-}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento inválido: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  printf '%s' "$value"
}

json_string() {
  printf '"%s"' "$(json_escape "$1")"
}

json_bool() {
  if [[ "$1" == "true" ]]; then
    printf 'true'
  else
    printf 'false'
  fi
}

fail_json() {
  local message="$1"
  printf '{"status":"failed","error":'
  json_string "$message"
  printf '}\n'
  exit 1
}

mark_run_failed() {
  local run_id="$1"
  local message="$2"
  [[ -n "$run_id" ]] || return
  [[ -f "$DB_PATH" ]] || return
  PRINTORA_MARK_RUN_ID="$run_id" \
  PRINTORA_MARK_DB_PATH="$DB_PATH" \
  PRINTORA_MARK_ERROR_MESSAGE="$message" \
  python - <<'PY' || true
import os
import sqlite3

db_path = os.environ["PRINTORA_MARK_DB_PATH"]
run_id = int(os.environ["PRINTORA_MARK_RUN_ID"])
message = os.environ["PRINTORA_MARK_ERROR_MESSAGE"]

with sqlite3.connect(db_path) as connection:
    connection.execute(
        """
        UPDATE app_update_runs
        SET status = 'failed',
            finished_at = CURRENT_TIMESTAMP,
            error_message = ?
        WHERE id = ? AND status = 'running'
        """,
        (message, run_id),
    )
    connection.execute(
        """
        UPDATE app_update_steps
        SET status = 'failed',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP,
            log_excerpt = COALESCE(log_excerpt, ?)
        WHERE run_id = ? AND status IN ('pending', 'running')
        """,
        (message[:4000], run_id),
    )
PY
}

mark_step() {
  local step_key="$1"
  local status="$2"
  local message="${3:-}"
  [[ -n "$UPDATE_RUN_ID" ]] || return
  [[ -f "$DB_PATH" ]] || return
  PRINTORA_MARK_RUN_ID="$UPDATE_RUN_ID" \
  PRINTORA_MARK_DB_PATH="$DB_PATH" \
  PRINTORA_MARK_STEP_KEY="$step_key" \
  PRINTORA_MARK_STEP_STATUS="$status" \
  PRINTORA_MARK_STEP_MESSAGE="$message" \
  python - <<'PY' || true
import os
import sqlite3

db_path = os.environ["PRINTORA_MARK_DB_PATH"]
run_id = int(os.environ["PRINTORA_MARK_RUN_ID"])
step_key = os.environ["PRINTORA_MARK_STEP_KEY"]
status = os.environ["PRINTORA_MARK_STEP_STATUS"]
message = os.environ.get("PRINTORA_MARK_STEP_MESSAGE", "")[:4000] or None

if status == "running":
    sql = """
        UPDATE app_update_steps
        SET status = 'running',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            log_excerpt = COALESCE(?, log_excerpt)
        WHERE run_id = ? AND step_key = ?
        """
elif status in {"succeeded", "skipped"}:
    sql = """
        UPDATE app_update_steps
        SET status = ?,
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP,
            log_excerpt = COALESCE(?, log_excerpt)
        WHERE run_id = ? AND step_key = ?
        """
else:
    sql = """
        UPDATE app_update_steps
        SET status = 'failed',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP,
            log_excerpt = COALESCE(?, log_excerpt)
        WHERE run_id = ? AND step_key = ?
        """

with sqlite3.connect(db_path) as connection:
    if status in {"succeeded", "skipped"}:
        connection.execute(sql, (status, message, run_id, step_key))
    else:
        connection.execute(sql, (message, run_id, step_key))
PY
}

mark_step_running() {
  mark_step "$1" "running" "${2:-}"
}

mark_step_succeeded() {
  mark_step "$1" "succeeded" "${2:-}"
}

on_error() {
  local exit_code="$1"
  local line_no="$2"
  if [[ "$MODE" == "apply" && -n "$UPDATE_RUN_ID" ]]; then
    mark_run_failed "$UPDATE_RUN_ID" "android_update_printora.sh falhou na linha ${line_no} com exit ${exit_code}"
  fi
}

trap 'on_error "$?" "$LINENO"' ERR

require_mode() {
  [[ -n "$MODE" ]] || fail_json "modo obrigatório: --plan, --apply ou --rollback"
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail_json "comando obrigatório não encontrado: ${command_name}"
}

validate_safe_path() {
  local path_value="$1"
  local label="$2"
  [[ -n "$path_value" ]] || fail_json "${label} vazio"
  [[ "$path_value" != "/" ]] || fail_json "${label} não pode ser /"
  [[ "$path_value" != "." ]] || fail_json "${label} não pode ser ."
}

validate_tag() {
  [[ -n "$TARGET_TAG" ]] || fail_json "--tag é obrigatório"
  [[ "$TARGET_TAG" =~ ^v[0-9]+[.][0-9]+[.][0-9]+([.-][A-Za-z0-9]+)*$ ]] || fail_json "tag inválida: ${TARGET_TAG}"
}

project_remote_url() {
  if [[ -n "$UPDATE_REMOTE_URL" ]]; then
    printf '%s' "$UPDATE_REMOTE_URL"
    return
  fi
  git -C "$ROOT_DIR" remote get-url origin 2>/dev/null || true
}

tag_exists_on_remote() {
  local remote_url="$1"
  [[ -n "$remote_url" ]] || fail_json "remote origin não configurado"
  git ls-remote --exit-code --tags "$remote_url" "refs/tags/${TARGET_TAG}" >/dev/null 2>&1
}

validate_common_plan_inputs() {
  require_command git
  require_command tmux
  require_command python
  validate_safe_path "$ROOT_DIR" "ROOT_DIR"
  [[ -d "$ROOT_DIR" ]] || fail_json "diretório atual do projeto não existe: ${ROOT_DIR}"
  [[ -f "$DB_PATH" || -d "$DATA_DIR" ]] || fail_json "banco SQLite ou data dir não existe: ${DB_PATH}"
  validate_tag
  local remote_url
  remote_url="$(project_remote_url)"
  if ! tag_exists_on_remote "$remote_url"; then
    fail_json "tag alvo não encontrada no repositório remoto: ${TARGET_TAG}"
  fi
}

steps_json() {
  cat <<'JSON'
[{"key":"validate_environment","title":"Validar git, tmux, python, projeto, data dir e tag remota"},{"key":"backup_database","title":"Criar backup obrigatório do printora.db"},{"key":"backup_project","title":"Preservar pasta atual como Printora.previous-update-<timestamp>"},{"key":"checkout_release","title":"Clonar release alvo em Printora.next"},{"key":"preserve_venv","title":"Preservar backend/.venv quando possível"},{"key":"install_backend","title":"Instalar backend editable sem dependências"},{"key":"apply_schema","title":"Inicializar backend para aplicar SQL idempotente"},{"key":"build_frontend","title":"Buildar frontend quando dist versionado não existir"},{"key":"restart_app","title":"Reiniciar sessões printora e printora-mdns"},{"key":"validate_health","title":"Validar /health"}]
JSON
}

print_plan_json() {
  local remote_url
  remote_url="$(project_remote_url)"
  printf '{"status":"planned","mode":"plan","target_tag":'
  json_string "$TARGET_TAG"
  printf ',"environment":"android_termux","root_dir":'
  json_string "$ROOT_DIR"
  printf ',"data_dir":'
  json_string "$DATA_DIR"
  printf ',"database_path":'
  json_string "$DB_PATH"
  printf ',"remote_url":'
  json_string "$remote_url"
  printf ',"will_modify_files":false,"steps":'
  steps_json
  printf '}\n'
}

timestamp_utc() {
  date -u +"%Y%m%dT%H%M%SZ"
}

backend_python() {
  if [[ -x "${NEXT_DIR}/backend/.venv/bin/python" ]]; then
    printf '%s' "${NEXT_DIR}/backend/.venv/bin/python"
    return
  fi
  if [[ -x "${ROOT_DIR}/backend/.venv/bin/python" ]]; then
    printf '%s' "${ROOT_DIR}/backend/.venv/bin/python"
    return
  fi
  printf '%s' "python"
}

copy_preserving() {
  local source_path="$1"
  local target_path="$2"
  validate_safe_path "$source_path" "source_path"
  validate_safe_path "$target_path" "target_path"
  [[ -e "$source_path" ]] || fail_json "origem não existe: ${source_path}"
  [[ ! -e "$target_path" ]] || fail_json "destino já existe: ${target_path}"
  mv "$source_path" "$target_path"
}

backup_database() {
  local timestamp="$1"
  local backup_path="${BACKUP_DIR}/printora.db.before-update-${timestamp}"
  mkdir -p "$BACKUP_DIR"
  if [[ -f "$DB_PATH" ]]; then
    cp "$DB_PATH" "$backup_path"
  else
    : >"$backup_path.empty-db-placeholder"
    backup_path="${backup_path}.empty-db-placeholder"
  fi
  printf '%s' "$backup_path"
}

clone_target_release() {
  local remote_url="$1"
  [[ ! -e "$NEXT_DIR" ]] || fail_json "diretório de próxima versão já existe: ${NEXT_DIR}"
  git clone --depth 1 --branch "$TARGET_TAG" "$remote_url" "$NEXT_DIR"
}

preserve_venv() {
  if [[ -d "${PREVIOUS_PATH}/backend/.venv" && ! -e "${NEXT_DIR}/backend/.venv" ]]; then
    mv "${PREVIOUS_PATH}/backend/.venv" "${NEXT_DIR}/backend/.venv"
  fi
}

install_backend() {
  (
    cd "$NEXT_DIR"
    "$(backend_python)" -m pip install -e backend --no-deps
  )
}

apply_schema() {
  (
    cd "$NEXT_DIR"
    PRINTORA_DATA_DIR="$DATA_DIR" "$(backend_python)" - <<'PY'
from app.config import get_settings
from app.database import initialize_database

settings = get_settings()
initialize_database(settings.database_path)
PY
  )
}

build_frontend_if_needed() {
  if [[ -s "${NEXT_DIR}/frontend/dist/index.html" ]]; then
    return
  fi
  require_command npm
  "${NEXT_DIR}/scripts/npm_frontend_install.sh" "${NEXT_DIR}/frontend" npm
  (
    cd "${NEXT_DIR}/frontend"
    node node_modules/typescript/bin/tsc -b
    node node_modules/vite/bin/vite.js build
  )
}

stop_tmux_sessions() {
  tmux kill-session -t printora 2>/dev/null || true
  tmux kill-session -t printora-mdns 2>/dev/null || true
}

restart_app() {
  tmux new-session -d -s printora "cd '$ROOT_DIR/backend' && export PRINTORA_DATA_DIR='$DATA_DIR' && . .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port '$HTTP_PORT'"
  tmux new-session -d -s printora-mdns "cd '$ROOT_DIR' && python scripts/android_mdns_printora.py --name '$HOST_NAME' --port '$PUBLIC_PORT'"
}

validate_health() {
  require_command curl
  for _ in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done
  fail_json "Printora não respondeu em ${HEALTH_URL}"
}

mark_run_succeeded() {
  local run_id="$1"
  local db_backup="$2"
  local previous_path="$3"
  [[ -n "$run_id" ]] || return
  PRINTORA_MARK_RUN_ID="$run_id" \
  PRINTORA_MARK_DB_PATH="$DB_PATH" \
  PRINTORA_MARK_BACKUP_DB_PATH="$db_backup" \
  PRINTORA_MARK_PREVIOUS_PATH="$previous_path" \
  PRINTORA_MARK_CURRENT_PATH="$ROOT_DIR" \
  python - <<'PY'
import os
import sqlite3

db_path = os.environ["PRINTORA_MARK_DB_PATH"]
run_id = int(os.environ["PRINTORA_MARK_RUN_ID"])
backup_db_path = os.environ["PRINTORA_MARK_BACKUP_DB_PATH"]
previous_path = os.environ["PRINTORA_MARK_PREVIOUS_PATH"]
current_path = os.environ["PRINTORA_MARK_CURRENT_PATH"]

with sqlite3.connect(db_path) as connection:
    connection.execute(
        """
        UPDATE app_update_runs
        SET status = 'succeeded',
            finished_at = CURRENT_TIMESTAMP,
            backup_db_path = ?,
            backup_project_path = ?,
            previous_project_path = ?,
            current_project_path = ?,
            error_message = NULL
        WHERE id = ?
        """,
        (backup_db_path, previous_path, previous_path, current_path, run_id),
    )
    connection.execute(
        """
        UPDATE app_update_steps
        SET status = 'succeeded',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP
        WHERE run_id = ?
        """,
        (run_id,),
    )
PY
}

apply_update() {
  mark_step_running "validate_environment"
  validate_common_plan_inputs
  mark_step_succeeded "validate_environment"
  require_command curl
  local remote_url timestamp db_backup previous_path
  remote_url="$(project_remote_url)"
  timestamp="$(timestamp_utc)"
  previous_path="${HOME}/Printora.previous-update-${timestamp}"
  mark_step_running "backup_database"
  db_backup="$(backup_database "$timestamp")"
  mark_step_succeeded "backup_database" "$db_backup"
  mark_step_running "backup_project"
  copy_preserving "$ROOT_DIR" "$previous_path"
  PREVIOUS_PATH="$previous_path"
  mark_step_succeeded "backup_project" "$previous_path"
  mark_step_running "checkout_release"
  clone_target_release "$remote_url"
  mark_step_succeeded "checkout_release" "$NEXT_DIR"
  mark_step_running "preserve_venv"
  preserve_venv
  mark_step_succeeded "preserve_venv"
  mark_step_running "install_backend"
  install_backend
  mark_step_succeeded "install_backend"
  mark_step_running "apply_schema"
  apply_schema
  mark_step_succeeded "apply_schema"
  mark_step_running "build_frontend"
  build_frontend_if_needed
  mark_step_succeeded "build_frontend"
  mark_step_running "restart_app"
  copy_preserving "$NEXT_DIR" "$ROOT_DIR"
  stop_tmux_sessions
  restart_app
  mark_step_succeeded "restart_app"
  mark_step_running "validate_health"
  validate_health
  mark_step_succeeded "validate_health"
  mark_run_succeeded "$UPDATE_RUN_ID" "$db_backup" "$previous_path"
  printf '{"status":"succeeded","mode":"apply","target_tag":'
  json_string "$TARGET_TAG"
  printf ',"backup_db_path":'
  json_string "$db_backup"
  printf ',"previous_project_path":'
  json_string "$previous_path"
  printf ',"current_project_path":'
  json_string "$ROOT_DIR"
  printf ',"health_url":'
  json_string "$HEALTH_URL"
  printf '}\n'
}

rollback_update() {
  [[ -n "$RUN_ID" || -n "$PREVIOUS_PATH" ]] || fail_json "--rollback exige --run-id ou --previous-path"
  [[ -n "$PREVIOUS_PATH" ]] || fail_json "--run-id ainda exige --previous-path neste script standalone"
  validate_safe_path "$ROOT_DIR" "ROOT_DIR"
  validate_safe_path "$PREVIOUS_PATH" "PREVIOUS_PATH"
  [[ -d "$PREVIOUS_PATH" ]] || fail_json "previous-path não existe: ${PREVIOUS_PATH}"
  local timestamp current_backup
  timestamp="$(timestamp_utc)"
  current_backup="${HOME}/Printora.failed-update-${timestamp}"
  stop_tmux_sessions
  if [[ -d "$ROOT_DIR" ]]; then
    copy_preserving "$ROOT_DIR" "$current_backup"
  fi
  copy_preserving "$PREVIOUS_PATH" "$ROOT_DIR"
  if [[ -n "$DB_BACKUP_PATH" ]]; then
    [[ -f "$DB_BACKUP_PATH" ]] || fail_json "backup de banco não existe: ${DB_BACKUP_PATH}"
    mkdir -p "$BACKUP_DIR"
    if [[ -f "$DB_PATH" ]]; then
      cp "$DB_PATH" "${BACKUP_DIR}/printora.db.before-rollback-${timestamp}"
    fi
    cp "$DB_BACKUP_PATH" "$DB_PATH"
  fi
  restart_app
  validate_health
  mark_run_succeeded "$UPDATE_RUN_ID" "$DB_BACKUP_PATH" "$PREVIOUS_PATH"
  printf '{"status":"rolled_back","mode":"rollback","run_id":'
  json_string "$RUN_ID"
  printf ',"restored_project_path":'
  json_string "$ROOT_DIR"
  printf ',"preserved_failed_project_path":'
  json_string "$current_backup"
  printf ',"restored_db_backup_path":'
  json_string "$DB_BACKUP_PATH"
  printf ',"health_url":'
  json_string "$HEALTH_URL"
  printf '}\n'
}

require_mode
case "$MODE" in
  plan)
    validate_common_plan_inputs
    print_plan_json
    ;;
  apply)
    apply_update
    ;;
  rollback)
    rollback_update
    ;;
  *)
    fail_json "modo inválido"
    ;;
esac
