#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

MODE=""
TARGET_TAG=""
RUN_ID=""
PREVIOUS_PATH=""
DB_BACKUP_PATH=""
UPDATE_RUN_ID="${PRINTORA_UPDATE_RUN_ID:-}"

ROOT_DIR="${ROOT_DIR:-${DEFAULT_ROOT_DIR}}"
DATA_DIR="${PRINTORA_DATA_DIR:-${HOME}/.local/share/printora}"
DB_PATH="${PRINTORA_DB_PATH:-${DATA_DIR}/printora.db}"
BACKUP_DIR="${PRINTORA_BACKUP_DIR:-${DATA_DIR}/backups}"
NEXT_DIR="${PRINTORA_NEXT_DIR:-${ROOT_DIR}.next}"
HTTP_PORT="${HTTP_PORT:-${PRINTORA_PORT:-8069}}"
HEALTH_URL="${PRINTORA_HEALTH_URL:-http://127.0.0.1:${HTTP_PORT}/health}"
UPDATE_REMOTE_URL="${PRINTORA_UPDATE_REMOTE_URL:-}"
SERVICE_NAME="${PRINTORA_SERVICE_NAME:-printora.service}"
OS_OVERRIDE="${PRINTORA_UPDATE_OS_OVERRIDE:-}"
SYSTEMD_OVERRIDE="${PRINTORA_UPDATE_SYSTEMD_OVERRIDE:-}"

usage() {
  cat <<'USAGE'
Uso:
  scripts/update_printora.sh --plan --tag vX.Y.Z
  scripts/update_printora.sh --apply --tag vX.Y.Z
  scripts/update_printora.sh --rollback --previous-path /path/anterior [--db-backup /path/backup.db]
  scripts/update_printora.sh --rollback --run-id ID --previous-path /path/anterior [--db-backup /path/backup.db]
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
  "$(python_bin)" - <<'PY' || true
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
  "$(python_bin)" - <<'PY' || true
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
    mark_run_failed "$UPDATE_RUN_ID" "update_printora.sh falhou na linha ${line_no} com exit ${exit_code}"
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

python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    printf '%s' "python"
  fi
}

detect_os() {
  if [[ -n "$OS_OVERRIDE" ]]; then
    printf '%s' "$OS_OVERRIDE"
    return
  fi
  case "$(uname -s)" in
    Darwin) printf '%s' "macos" ;;
    Linux) printf '%s' "linux" ;;
    *) printf '%s' "unknown" ;;
  esac
}

has_systemd() {
  if [[ -n "$SYSTEMD_OVERRIDE" ]]; then
    [[ "$SYSTEMD_OVERRIDE" == "true" ]]
    return
  fi
  [[ -d /run/systemd/system ]] && command -v systemctl >/dev/null 2>&1
}

systemd_scope() {
  if ! has_systemd; then
    printf '%s' "none"
    return
  fi
  if systemctl --user list-unit-files "$SERVICE_NAME" >/dev/null 2>&1 || systemctl --user status "$SERVICE_NAME" >/dev/null 2>&1; then
    printf '%s' "user"
    return
  fi
  if systemctl list-unit-files "$SERVICE_NAME" >/dev/null 2>&1 || systemctl status "$SERVICE_NAME" >/dev/null 2>&1; then
    printf '%s' "system"
    return
  fi
  printf '%s' "none"
}

restart_mode() {
  local os_name scope
  os_name="$(detect_os)"
  scope="$(systemd_scope)"
  if [[ "$scope" != "none" ]]; then
    printf 'systemd_%s' "$scope"
    return
  fi
  if command -v tmux >/dev/null 2>&1 && tmux has-session -t printora >/dev/null 2>&1; then
    printf '%s' "tmux"
    return
  fi
  if [[ -x "${ROOT_DIR}/scripts/run_app.sh" ]]; then
    printf '%s' "runner"
    return
  fi
  if [[ "$os_name" == "macos" || "$os_name" == "linux" ]]; then
    printf '%s' "manual"
    return
  fi
  printf '%s' "unknown"
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
    normalize_remote_url "$UPDATE_REMOTE_URL"
    return
  fi
  git -C "$ROOT_DIR" remote get-url origin 2>/dev/null || true
}

normalize_remote_url() {
  local remote_url="$1"
  if [[ "$remote_url" =~ ^https://github[.]com/[^/]+/[^/]+/releases/tag/ ]]; then
    remote_url="${remote_url%%/releases/tag/*}.git"
  fi
  printf '%s' "$remote_url"
}

tag_exists_on_remote() {
  local remote_url="$1"
  [[ -n "$remote_url" ]] || fail_json "remote origin não configurado"
  git ls-remote --exit-code --tags "$remote_url" "refs/tags/${TARGET_TAG}" >/dev/null 2>&1
}

validate_common_plan_inputs() {
  require_command git
  [[ -n "$(python_bin)" ]] || fail_json "comando obrigatório não encontrado: python3/python"
  require_command curl
  validate_safe_path "$ROOT_DIR" "ROOT_DIR"
  [[ -d "$ROOT_DIR" ]] || fail_json "diretório do projeto não existe: ${ROOT_DIR}"
  [[ -f "$DB_PATH" || -d "$DATA_DIR" ]] || fail_json "banco SQLite ou data dir não existe: ${DB_PATH}"
  validate_tag
  local os_name mode remote_url
  os_name="$(detect_os)"
  [[ "$os_name" == "macos" || "$os_name" == "linux" ]] || fail_json "sistema Unix não suportado: ${os_name}"
  mode="$(restart_mode)"
  [[ "$mode" != "unknown" ]] || fail_json "modo de restart não detectado"
  remote_url="$(project_remote_url)"
  if ! tag_exists_on_remote "$remote_url"; then
    fail_json "tag alvo não encontrada no repositório remoto: ${TARGET_TAG}"
  fi
}

steps_json() {
  cat <<'JSON'
[{"key":"validate_environment","title":"Validar git, python, curl, projeto, data dir, restart e tag remota"},{"key":"backup_database","title":"Criar backup obrigatório do printora.db"},{"key":"backup_project","title":"Preservar pasta atual como Printora.previous-update-<timestamp>"},{"key":"checkout_release","title":"Clonar release alvo em Printora.next"},{"key":"preserve_venv","title":"Preservar backend/.venv quando possível"},{"key":"install_backend","title":"Instalar backend editable sem dependências"},{"key":"apply_schema","title":"Inicializar backend para aplicar SQL idempotente"},{"key":"build_frontend","title":"Buildar frontend quando dist versionado não existir"},{"key":"restart_app","title":"Reiniciar por systemd, tmux ou runner local"},{"key":"validate_health","title":"Validar /health"}]
JSON
}

print_plan_json() {
  local os_name mode remote_url systemd_available
  os_name="$(detect_os)"
  mode="$(restart_mode)"
  remote_url="$(project_remote_url)"
  if has_systemd; then
    systemd_available="true"
  else
    systemd_available="false"
  fi
  printf '{"status":"planned","mode":"plan","target_tag":'
  json_string "$TARGET_TAG"
  printf ',"environment":"unix","platform":'
  json_string "$os_name"
  printf ',"restart_mode":'
  json_string "$mode"
  printf ',"systemd_available":'
  json_bool "$systemd_available"
  printf ',"root_dir":'
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
  python_bin
}

move_preserving() {
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
  if [[ -d "${ROOT_DIR}/backend/.venv" && ! -e "${NEXT_DIR}/backend/.venv" ]]; then
    cp -a "${ROOT_DIR}/backend/.venv" "${NEXT_DIR}/backend/.venv"
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
  npm --prefix "${NEXT_DIR}/frontend" run build
}

project_previous_path() {
  local timestamp="$1"
  local parent base
  parent="$(dirname "$ROOT_DIR")"
  base="$(basename "$ROOT_DIR")"
  printf '%s/%s.previous-update-%s' "$parent" "$base" "$timestamp"
}

replace_project() {
  local previous_path="$1"
  local parent
  parent="$(dirname "$ROOT_DIR")"
  cd "$parent"
  move_preserving "$ROOT_DIR" "$previous_path"
  move_preserving "$NEXT_DIR" "$ROOT_DIR"
}

restart_systemd() {
  local mode="$1"
  case "$mode" in
    systemd_user)
      systemctl --user restart "$SERVICE_NAME"
      ;;
    systemd_system)
      systemctl restart "$SERVICE_NAME"
      ;;
    *)
      return 1
      ;;
  esac
}

restart_tmux() {
  tmux kill-session -t printora 2>/dev/null || true
  tmux new-session -d -s printora "cd '$ROOT_DIR' && PRINTORA_DATA_DIR='$DATA_DIR' PRINTORA_PORT='$HTTP_PORT' scripts/run_app.sh --no-open --foreground"
}

restart_runner() {
  "${ROOT_DIR}/scripts/run_app.sh" --stop >/dev/null 2>&1 || true
  PRINTORA_DATA_DIR="$DATA_DIR" PRINTORA_PORT="$HTTP_PORT" "${ROOT_DIR}/scripts/run_app.sh" --no-open
}

restart_app() {
  local mode
  mode="$(restart_mode)"
  case "$mode" in
    systemd_user|systemd_system)
      restart_systemd "$mode"
      ;;
    tmux)
      restart_tmux
      ;;
    runner|manual)
      restart_runner
      ;;
    *)
      fail_json "modo de restart não suportado: ${mode}"
      ;;
  esac
}

validate_health() {
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
  [[ -f "$DB_PATH" ]] || return
  PRINTORA_MARK_RUN_ID="$run_id" \
  PRINTORA_MARK_DB_PATH="$DB_PATH" \
  PRINTORA_MARK_BACKUP_DB_PATH="$db_backup" \
  PRINTORA_MARK_PREVIOUS_PATH="$previous_path" \
  PRINTORA_MARK_CURRENT_PATH="$ROOT_DIR" \
  "$(python_bin)" - <<'PY' || true
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
  local remote_url timestamp db_backup previous_path
  remote_url="$(project_remote_url)"
  timestamp="$(timestamp_utc)"
  previous_path="$(project_previous_path "$timestamp")"
  mark_step_running "backup_database"
  db_backup="$(backup_database "$timestamp")"
  mark_step_succeeded "backup_database" "$db_backup"
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
  mark_step_running "backup_project"
  replace_project "$previous_path"
  PREVIOUS_PATH="$previous_path"
  mark_step_succeeded "backup_project" "$previous_path"
  mark_step_running "restart_app"
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
  current_backup="$(dirname "$ROOT_DIR")/$(basename "$ROOT_DIR").failed-update-${timestamp}"
  if [[ -d "$ROOT_DIR" ]]; then
    move_preserving "$ROOT_DIR" "$current_backup"
  fi
  move_preserving "$PREVIOUS_PATH" "$ROOT_DIR"
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
