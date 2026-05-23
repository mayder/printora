import platform
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


UpdateEnvironment = Literal["android_termux", "unix", "windows", "unknown"]
UpdateRunStatus = Literal["planned", "running", "succeeded", "failed", "rolled_back"]
UpdateStepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]


class UpdatePlanRequest(BaseModel):
    target_tag: str = Field(min_length=1, max_length=80)
    source_url: str | None = Field(default=None, max_length=500)


class UpdateApplyRequest(BaseModel):
    target_tag: str = Field(min_length=1, max_length=80)
    confirmation_phrase: str = Field(min_length=1, max_length=120)
    source_url: str | None = Field(default=None, max_length=500)


class UpdateStepRecord(BaseModel):
    id: int
    run_id: int
    step_key: str
    title: str
    status: UpdateStepStatus
    log_excerpt: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class UpdateRunRecord(BaseModel):
    id: int
    target_version: str
    target_tag: str
    source_url: str | None = None
    environment: UpdateEnvironment
    status: UpdateRunStatus
    started_at: str | None = None
    finished_at: str | None = None
    backup_db_path: str | None = None
    backup_project_path: str | None = None
    previous_project_path: str | None = None
    current_project_path: str | None = None
    error_message: str | None = None
    created_at: str
    steps: list[UpdateStepRecord] = Field(default_factory=list)


class UpdatePlanResponse(BaseModel):
    safe_mode: str = "plan_only"
    update_supported: bool
    can_apply: bool = False
    message: str
    run: UpdateRunRecord


class UpdateHistoryResponse(BaseModel):
    runs: list[UpdateRunRecord]


class UpdateApplyResponse(BaseModel):
    accepted: bool
    message: str
    run: UpdateRunRecord
    script_stdout: str | None = None
    script_stderr: str | None = None


class SelfUpdateRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create_plan(
        self,
        *,
        target_tag: str,
        source_url: str | None,
        environment: UpdateEnvironment,
        current_project_path: str,
        steps: list[tuple[str, str]],
    ) -> UpdateRunRecord:
        target_version = target_tag.removeprefix("v")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO app_update_runs (
                    target_version, target_tag, source_url, environment, status, current_project_path
                )
                VALUES (?, ?, ?, ?, 'planned', ?)
                """,
                (target_version, target_tag, source_url, environment, current_project_path),
            )
            run_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO app_update_steps (run_id, step_key, title, status)
                VALUES (?, ?, ?, 'pending')
                """,
                [(run_id, step_key, title) for step_key, title in steps],
            )
        record = self.get_run(run_id)
        if record is None:
            raise RuntimeError("update run was not persisted")
        return record

    def create_run(
        self,
        *,
        target_tag: str,
        source_url: str | None,
        environment: UpdateEnvironment,
        current_project_path: str,
        status: UpdateRunStatus,
        steps: list[tuple[str, str]],
    ) -> UpdateRunRecord:
        target_version = target_tag.removeprefix("v")
        started_at = "CURRENT_TIMESTAMP" if status == "running" else "NULL"
        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                INSERT INTO app_update_runs (
                    target_version, target_tag, source_url, environment, status, started_at, current_project_path
                )
                VALUES (?, ?, ?, ?, ?, {started_at}, ?)
                """,
                (target_version, target_tag, source_url, environment, status, current_project_path),
            )
            run_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO app_update_steps (run_id, step_key, title, status)
                VALUES (?, ?, ?, 'pending')
                """,
                [(run_id, step_key, title) for step_key, title in steps],
            )
        record = self.get_run(run_id)
        if record is None:
            raise RuntimeError("update run was not persisted")
        return record

    def has_running_update(self) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM app_update_runs WHERE status = 'running' LIMIT 1"
            ).fetchone()
        return row is not None

    def mark_all_steps(self, run_id: int, status: UpdateStepStatus, log_excerpt: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE app_update_steps
                SET status = ?,
                    log_excerpt = COALESCE(?, log_excerpt),
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                    finished_at = CASE WHEN ? IN ('succeeded', 'failed', 'skipped') THEN CURRENT_TIMESTAMP ELSE finished_at END
                WHERE run_id = ?
                """,
                (status, log_excerpt, status, run_id),
            )

    def finish_run(
        self,
        run_id: int,
        *,
        status: UpdateRunStatus,
        error_message: str | None = None,
        backup_db_path: str | None = None,
        backup_project_path: str | None = None,
        previous_project_path: str | None = None,
        current_project_path: str | None = None,
    ) -> UpdateRunRecord:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE app_update_runs
                SET status = ?,
                    finished_at = CURRENT_TIMESTAMP,
                    error_message = ?,
                    backup_db_path = COALESCE(?, backup_db_path),
                    backup_project_path = COALESCE(?, backup_project_path),
                    previous_project_path = COALESCE(?, previous_project_path),
                    current_project_path = COALESCE(?, current_project_path)
                WHERE id = ?
                """,
                (
                    status,
                    error_message,
                    backup_db_path,
                    backup_project_path,
                    previous_project_path,
                    current_project_path,
                    run_id,
                ),
            )
        record = self.get_run(run_id)
        if record is None:
            raise RuntimeError("update run not found after finish")
        return record

    def list_runs(self, limit: int = 20) -> list[UpdateRunRecord]:
        clean_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM app_update_runs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (clean_limit,),
            ).fetchall()
            runs = [_run_from_row(row) for row in rows]
            steps_by_run = self._steps_by_run(connection, [run.id for run in runs])
        return [run.model_copy(update={"steps": steps_by_run.get(run.id, [])}) for run in runs]

    def get_run(self, run_id: int) -> UpdateRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM app_update_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                return None
            run = _run_from_row(row)
            steps = self._steps_by_run(connection, [run.id]).get(run.id, [])
        return run.model_copy(update={"steps": steps})

    def _steps_by_run(
        self,
        connection: sqlite3.Connection,
        run_ids: list[int],
    ) -> dict[int, list[UpdateStepRecord]]:
        if not run_ids:
            return {}
        placeholders = ",".join("?" for _ in run_ids)
        rows = connection.execute(
            f"""
            SELECT *
            FROM app_update_steps
            WHERE run_id IN ({placeholders})
            ORDER BY id
            """,
            run_ids,
        ).fetchall()
        result: dict[int, list[UpdateStepRecord]] = {}
        for row in rows:
            step = _step_from_row(row)
            result.setdefault(step.run_id, []).append(step)
        return result

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def build_update_plan(
    *,
    repository: SelfUpdateRepository,
    request: UpdatePlanRequest,
    project_root: Path,
    environment: UpdateEnvironment | None = None,
) -> UpdatePlanResponse:
    detected_environment = environment or detect_update_environment()
    if detected_environment == "unknown":
        raise ValueError("Ambiente não suportado para update do Printora.")
    run = repository.create_plan(
        target_tag=request.target_tag,
        source_url=request.source_url,
        environment=detected_environment,
        current_project_path=str(project_root),
        steps=_steps_for_environment(detected_environment),
    )
    return UpdatePlanResponse(
        update_supported=detected_environment == "android_termux",
        can_apply=detected_environment == "android_termux",
        message="Plano criado. Nenhum arquivo foi alterado.",
        run=run,
    )


def apply_self_update(
    *,
    repository: SelfUpdateRepository,
    request: UpdateApplyRequest,
    project_root: Path,
    script_path: Path,
    stable_release_tags: set[str],
    timeout_seconds: float,
    environment: UpdateEnvironment | None = None,
) -> UpdateApplyResponse:
    _validate_confirmation(request.confirmation_phrase)
    _validate_release_tag(request.target_tag, stable_release_tags)
    detected_environment = environment or detect_update_environment()
    if detected_environment != "android_termux":
        raise ValueError(f"not_supported: update real disponível apenas no Android/Termux; ambiente atual={detected_environment}")
    if repository.has_running_update():
        raise ValueError("Já existe update em execução.")
    if not script_path.is_file():
        raise ValueError(f"Script de update não encontrado: {script_path}")

    plan_result = _run_update_script(
        script_path=script_path,
        mode="--plan",
        target_tag=request.target_tag,
        project_root=project_root,
        timeout_seconds=timeout_seconds,
    )
    plan_stdout = sanitize_log(plan_result.stdout)
    plan_stderr = sanitize_log(plan_result.stderr)
    if plan_result.returncode != 0:
        run = repository.create_run(
            target_tag=request.target_tag,
            source_url=request.source_url,
            environment=detected_environment,
            current_project_path=str(project_root),
            status="failed",
            steps=_steps_for_environment(detected_environment),
        )
        repository.mark_all_steps(run.id, "failed", plan_stdout or plan_stderr)
        run = repository.finish_run(run.id, status="failed", error_message=plan_stdout or plan_stderr or "Falha no plano do script.")
        return UpdateApplyResponse(accepted=False, message="Falha ao gerar plano pelo script.", run=run, script_stdout=plan_stdout, script_stderr=plan_stderr)

    run = repository.create_run(
        target_tag=request.target_tag,
        source_url=request.source_url,
        environment=detected_environment,
        current_project_path=str(project_root),
        status="running",
        steps=_steps_for_environment(detected_environment),
    )
    repository.mark_all_steps(run.id, "running", plan_stdout)

    if _should_detach_android_apply(project_root):
        _start_update_script_detached(
            script_path=script_path,
            mode="--apply",
            target_tag=request.target_tag,
            project_root=project_root,
            run_id=run.id,
        )
        run = repository.get_run(run.id) or run
        return UpdateApplyResponse(
            accepted=True,
            message="Update Android/Termux iniciado. O Printora pode reiniciar; acompanhe pelo histórico.",
            run=run,
            script_stdout=plan_stdout,
            script_stderr=plan_stderr,
        )

    apply_result = _run_update_script(
        script_path=script_path,
        mode="--apply",
        target_tag=request.target_tag,
        project_root=project_root,
        timeout_seconds=timeout_seconds,
        run_id=run.id,
    )
    stdout = sanitize_log(apply_result.stdout)
    stderr = sanitize_log(apply_result.stderr)
    payload = _json_object_from_stdout(apply_result.stdout)
    if apply_result.returncode == 0:
        repository.mark_all_steps(run.id, "succeeded", stdout)
        run = repository.finish_run(
            run.id,
            status="succeeded",
            backup_db_path=_optional_payload_str(payload, "backup_db_path"),
            backup_project_path=_optional_payload_str(payload, "previous_project_path"),
            previous_project_path=_optional_payload_str(payload, "previous_project_path"),
            current_project_path=_optional_payload_str(payload, "current_project_path") or str(project_root),
        )
        return UpdateApplyResponse(accepted=True, message="Update Android/Termux aplicado pelo script.", run=run, script_stdout=stdout, script_stderr=stderr)

    repository.mark_all_steps(run.id, "failed", stdout or stderr)
    run = repository.finish_run(run.id, status="failed", error_message=stdout or stderr or "Falha ao aplicar update.")
    return UpdateApplyResponse(accepted=False, message="Update Android/Termux falhou. Consulte histórico.", run=run, script_stdout=stdout, script_stderr=stderr)


def sanitize_log(value: str, max_length: int = 4000) -> str:
    clean = re.sub(r"(?i)(token|secret|password|passwd|api[_-]?key)=\\S+", r"\1=<redacted>", value)
    clean = clean.replace("\x00", "")
    return clean[-max_length:]


def detect_update_environment() -> UpdateEnvironment:
    if _is_termux():
        return "android_termux"
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system in {"linux", "darwin"}:
        return "unix"
    return "unknown"


def _is_termux() -> bool:
    prefixes = [
        Path("/data/data/com.termux/files/usr"),
        Path.home() / "../usr",
    ]
    return any(path.exists() for path in prefixes)


def _validate_confirmation(confirmation_phrase: str) -> None:
    if confirmation_phrase != "ATUALIZAR PRINTORA":
        raise ValueError("Confirmação obrigatória inválida.")


def _validate_release_tag(target_tag: str, stable_release_tags: set[str]) -> None:
    if not target_tag or not re.fullmatch(r"v[0-9]+[.][0-9]+[.][0-9]+", target_tag):
        raise ValueError("Tag inválida para update.")
    if target_tag not in stable_release_tags:
        raise ValueError("Tag não pertence às releases estáveis disponíveis.")


def _run_update_script(
    *,
    script_path: Path,
    mode: str,
    target_tag: str,
    project_root: Path,
    timeout_seconds: float,
    run_id: int | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

    env = os.environ.copy()
    if run_id is not None:
        env["PRINTORA_UPDATE_RUN_ID"] = str(run_id)
    return subprocess.run(
        ["bash", str(script_path), mode, "--tag", target_tag],
        cwd=str(project_root),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )


def _start_update_script_detached(
    *,
    script_path: Path,
    mode: str,
    target_tag: str,
    project_root: Path,
    run_id: int,
) -> None:
    import os

    env = os.environ.copy()
    env["PRINTORA_UPDATE_RUN_ID"] = str(run_id)
    subprocess.Popen(
        ["bash", str(script_path), mode, "--tag", target_tag],
        cwd=str(project_root),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def _should_detach_android_apply(project_root: Path) -> bool:
    if sys.platform == "win32":
        return False
    return str(project_root).startswith("/data/data/com.termux/")


def _json_object_from_stdout(stdout: str) -> dict[str, Any]:
    import json

    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _optional_payload_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return str(value) if value else None


def _steps_for_environment(environment: UpdateEnvironment) -> list[tuple[str, str]]:
    common = [
        ("validate_target", "Validar release alvo"),
        ("backup_database", "Planejar backup obrigatório do banco"),
        ("backup_project", "Planejar preservação da versão atual do projeto"),
        ("checkout_release", "Planejar checkout/download da release"),
        ("install_backend", "Planejar reinstalação do backend"),
        ("apply_schema", "Planejar aplicação segura dos scripts SQL"),
        ("build_frontend", "Planejar build ou uso do frontend versionado"),
        ("restart_app", "Planejar reinício do Printora"),
        ("validate_health", "Planejar validação final de /health"),
    ]
    if environment == "android_termux":
        return [
            ("detect_termux", "Detectar Termux, tmux, Python, Node e porta ativa"),
            *common,
            ("restart_mdns", "Planejar reinício do anúncio printora.local"),
        ]
    if environment == "windows":
        return [
            ("detect_windows", "Detectar Python, npm, Git e PowerShell"),
            *common,
        ]
    return [
        ("detect_unix", "Detectar shell, Python, npm, Git e modo de restart"),
        *common,
    ]


def _run_from_row(row: sqlite3.Row) -> UpdateRunRecord:
    return UpdateRunRecord(
        id=int(row["id"]),
        target_version=str(row["target_version"]),
        target_tag=str(row["target_tag"]),
        source_url=row["source_url"],
        environment=row["environment"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        backup_db_path=row["backup_db_path"],
        backup_project_path=row["backup_project_path"],
        previous_project_path=row["previous_project_path"],
        current_project_path=row["current_project_path"],
        error_message=row["error_message"],
        created_at=str(row["created_at"]),
    )


def _step_from_row(row: sqlite3.Row) -> UpdateStepRecord:
    return UpdateStepRecord(
        id=int(row["id"]),
        run_id=int(row["run_id"]),
        step_key=str(row["step_key"]),
        title=str(row["title"]),
        status=row["status"],
        log_excerpt=row["log_excerpt"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )
