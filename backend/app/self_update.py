import platform
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.auth import scoped_where_clause


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


class UpdateRollbackRequest(BaseModel):
    run_id: int = Field(gt=0)
    confirmation_phrase: str = Field(min_length=1, max_length=120)


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


class UpdateReconcileResponse(BaseModel):
    safe_mode: str = "metadata_only"
    reconciled: int
    running_updates: int
    message: str
    runs: list[UpdateRunRecord]


class UpdateApplyResponse(BaseModel):
    accepted: bool
    message: str
    run: UpdateRunRecord
    script_stdout: str | None = None
    script_stderr: str | None = None


class UpdateRollbackResponse(BaseModel):
    accepted: bool
    message: str
    source_run: UpdateRunRecord
    rollback_run: UpdateRunRecord
    script_stdout: str | None = None
    script_stderr: str | None = None


class SelfUpdateRepository:
    def __init__(self, database_path: Path, user_id: int | None = None, organization_ids: tuple[int, ...] = ()) -> None:
        self.database_path = database_path
        self.user_id = user_id
        self.organization_ids = organization_ids

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
                    target_version, target_tag, source_url, environment, status, current_project_path, owner_user_id
                )
                VALUES (?, ?, ?, ?, 'planned', ?, ?)
                """,
                (target_version, target_tag, source_url, environment, current_project_path, self.user_id),
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
                    target_version, target_tag, source_url, environment, status, started_at, current_project_path, owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, {started_at}, ?, ?)
                """,
                (target_version, target_tag, source_url, environment, status, current_project_path, self.user_id),
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
        return self.count_running_updates() > 0

    def count_running_updates(self) -> int:
        with self._connect() as connection:
            scope_sql, params = self._scope_sql("app_update_runs", prefix="AND")
            row = connection.execute(
                f"SELECT COUNT(*) FROM app_update_runs WHERE status = 'running' {scope_sql}",
                params,
            ).fetchone()
        return int(row[0])

    def reconcile_interrupted_updates(self, *, installed_version: str, stale_after_minutes: int = 30) -> int:
        clean_installed_version = _normalize_version(installed_version)
        stale_interval = f"-{max(1, stale_after_minutes)} minutes"
        reconciled = 0
        with self._connect() as connection:
            scope_sql, params = self._scope_sql("app_update_runs", prefix="AND")
            rows = connection.execute(
                f"""
                SELECT *,
                    COALESCE(started_at, created_at) <= datetime('now', ?) AS is_stale
                FROM app_update_runs
                WHERE status = 'running'
                {scope_sql}
                ORDER BY created_at, id
                """,
                (stale_interval, *params),
            ).fetchall()
            for row in rows:
                target_matches = clean_installed_version in {
                    _normalize_version(str(row["target_version"])),
                    _normalize_version(str(row["target_tag"])),
                }
                if target_matches:
                    _finish_interrupted_run(
                        connection,
                        run_id=int(row["id"]),
                        run_status="succeeded",
                        step_status="skipped",
                        message=(
                            "Update reconciliado apos reinicio: a versao instalada "
                            f"{installed_version} ja corresponde ao alvo {row['target_tag']}."
                        ),
                    )
                    reconciled += 1
                    continue
                if bool(row["is_stale"]):
                    _finish_interrupted_run(
                        connection,
                        run_id=int(row["id"]),
                        run_status="failed",
                        step_status="failed",
                        message=(
                            "Update em execucao ficou orfao apos reinicio e a versao instalada "
                            f"{installed_version} nao corresponde ao alvo {row['target_tag']}."
                        ),
                    )
                    reconciled += 1
        return reconciled

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

    def add_step(
        self,
        run_id: int,
        *,
        step_key: str,
        title: str,
        status: UpdateStepStatus,
        log_excerpt: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_update_steps (run_id, step_key, title, status, log_excerpt)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, step_key, title, status, log_excerpt),
            )

    def list_runs(self, limit: int = 20) -> list[UpdateRunRecord]:
        clean_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            where_clause, params = self._scope_sql("app_update_runs", prefix="WHERE")
            rows = connection.execute(
                f"""
                SELECT *
                FROM app_update_runs
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (*params, clean_limit),
            ).fetchall()
            runs = [_run_from_row(row) for row in rows]
            steps_by_run = self._steps_by_run(connection, [run.id for run in runs])
        return [run.model_copy(update={"steps": steps_by_run.get(run.id, [])}) for run in runs]

    def get_run(self, run_id: int) -> UpdateRunRecord | None:
        with self._connect() as connection:
            scope_sql, params = self._scope_sql("app_update_runs", prefix="AND")
            row = connection.execute(
                f"SELECT * FROM app_update_runs WHERE id = ? {scope_sql}",
                (run_id, *params),
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

    def _scope_sql(self, table_alias: str, *, prefix: str) -> tuple[str, tuple[object, ...]]:
        if self.user_id is None:
            return "", ()
        where_clause, params = scoped_where_clause(table_alias, self.user_id, self.organization_ids)
        if prefix == "AND":
            return where_clause.replace("WHERE", "AND", 1), params
        return where_clause, params


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
        update_supported=detected_environment in {"android_termux", "unix", "windows"},
        can_apply=detected_environment in {"android_termux", "unix", "windows"},
        message="Plano criado. Nenhum arquivo foi alterado.",
        run=run,
    )


def apply_self_update(
    *,
    repository: SelfUpdateRepository,
    request: UpdateApplyRequest,
    project_root: Path,
    script_path: Path | None,
    stable_release_tags: set[str] | None,
    timeout_seconds: float,
    android_script_path: Path | None = None,
    unix_script_path: Path | None = None,
    windows_script_path: Path | None = None,
    environment: UpdateEnvironment | None = None,
) -> UpdateApplyResponse:
    from app.releases import installed_app_version

    _validate_confirmation(request.confirmation_phrase)
    _validate_release_tag(request.target_tag, stable_release_tags)
    detected_environment = environment or detect_update_environment()
    if detected_environment not in {"android_termux", "unix", "windows"}:
        raise ValueError(f"not_supported: update real disponível apenas em Android/Termux, Unix e Windows; ambiente atual={detected_environment}")
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    if repository.has_running_update():
        raise ValueError("Já existe update em execução.")
    selected_script_path = _script_path_for_environment(
        detected_environment,
        override_script_path=script_path,
        android_script_path=android_script_path,
        unix_script_path=unix_script_path,
        windows_script_path=windows_script_path,
    )
    if not selected_script_path.is_file():
        raise ValueError(f"Script de update não encontrado: {selected_script_path}")

    plan_result = _run_update_script(
        script_path=selected_script_path,
        mode="--plan",
        target_tag=request.target_tag,
        source_url=request.source_url,
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

    if _should_detach_self_update(detected_environment, project_root):
        log_path = _detached_update_log_path(repository.database_path, run.id)
        _start_update_script_detached(
            script_path=selected_script_path,
            mode="--apply",
            target_tag=request.target_tag,
            source_url=request.source_url,
            project_root=project_root,
            run_id=run.id,
            log_path=log_path,
        )
        run = repository.get_run(run.id) or run
        return UpdateApplyResponse(
            accepted=True,
            message=f"Update do Printora iniciado. O app pode reiniciar; acompanhe pelo histórico. Log: {log_path}",
            run=run,
            script_stdout=plan_stdout,
            script_stderr=plan_stderr,
        )

    apply_result = _run_update_script(
        script_path=selected_script_path,
        mode="--apply",
        target_tag=request.target_tag,
        source_url=request.source_url,
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
        return UpdateApplyResponse(accepted=True, message="Update do Printora aplicado pelo script.", run=run, script_stdout=stdout, script_stderr=stderr)

    repository.mark_all_steps(run.id, "failed", stdout or stderr)
    run = repository.finish_run(run.id, status="failed", error_message=stdout or stderr or "Falha ao aplicar update.")
    return UpdateApplyResponse(accepted=False, message="Update do Printora falhou. Consulte histórico.", run=run, script_stdout=stdout, script_stderr=stderr)


def rollback_self_update(
    *,
    repository: SelfUpdateRepository,
    request: UpdateRollbackRequest,
    project_root: Path,
    script_path: Path | None,
    timeout_seconds: float,
    android_script_path: Path | None = None,
    unix_script_path: Path | None = None,
    windows_script_path: Path | None = None,
) -> UpdateRollbackResponse:
    from app.releases import installed_app_version

    _validate_rollback_confirmation(request.confirmation_phrase)
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    if repository.has_running_update():
        raise ValueError("Já existe update em execução.")
    source_run = repository.get_run(request.run_id)
    if source_run is None:
        raise ValueError("Run de update não encontrado.")
    if source_run.status != "succeeded":
        raise ValueError("Rollback permitido apenas para update concluído com sucesso.")
    previous_path = _require_safe_previous_path(source_run.previous_project_path, project_root)
    db_backup_path = _safe_optional_db_backup_path(source_run.backup_db_path, repository.database_path)
    selected_script_path = _script_path_for_environment(
        source_run.environment,
        override_script_path=script_path,
        android_script_path=android_script_path,
        unix_script_path=unix_script_path,
        windows_script_path=windows_script_path,
    )
    if not selected_script_path.is_file():
        raise ValueError(f"Script de rollback não encontrado: {selected_script_path}")

    rollback_run = repository.create_run(
        target_tag=source_run.target_tag,
        source_url=f"rollback_of:{source_run.id}",
        environment=source_run.environment,
        current_project_path=str(project_root),
        status="running",
        steps=_rollback_steps_for_environment(source_run.environment),
    )
    repository.mark_all_steps(rollback_run.id, "running", f"rollback_of={source_run.id}")

    if _should_detach_self_update(source_run.environment, project_root):
        log_path = _detached_update_log_path(repository.database_path, rollback_run.id)
        _start_update_script_detached(
            script_path=selected_script_path,
            mode="--rollback",
            target_tag=source_run.target_tag,
            source_url=None,
            project_root=project_root,
            run_id=rollback_run.id,
            extra_args=_rollback_extra_args(source_run.id, previous_path, db_backup_path),
            log_path=log_path,
        )
        rollback_run = repository.get_run(rollback_run.id) or rollback_run
        return UpdateRollbackResponse(
            accepted=True,
            message=f"Rollback do Printora iniciado. O app pode reiniciar; acompanhe pelo histórico. Log: {log_path}",
            source_run=source_run,
            rollback_run=rollback_run,
        )

    rollback_result = _run_update_script(
        script_path=selected_script_path,
        mode="--rollback",
        target_tag=source_run.target_tag,
        source_url=None,
        project_root=project_root,
        timeout_seconds=timeout_seconds,
        run_id=rollback_run.id,
        extra_args=_rollback_extra_args(source_run.id, previous_path, db_backup_path),
    )
    stdout = sanitize_log(rollback_result.stdout)
    stderr = sanitize_log(rollback_result.stderr)
    if rollback_result.returncode == 0:
        repository.mark_all_steps(rollback_run.id, "succeeded", stdout)
        rollback_run = repository.finish_run(
            rollback_run.id,
            status="succeeded",
            backup_db_path=db_backup_path,
            previous_project_path=previous_path,
            current_project_path=str(project_root),
        )
        source_run = repository.finish_run(source_run.id, status="rolled_back")
        repository.add_step(
            source_run.id,
            step_key="rollback_completed",
            title=f"Rollback registrado pelo run {rollback_run.id}",
            status="succeeded",
            log_excerpt=stdout,
        )
        return UpdateRollbackResponse(
            accepted=True,
            message="Rollback do Printora aplicado pelo script.",
            source_run=source_run,
            rollback_run=rollback_run,
            script_stdout=stdout,
            script_stderr=stderr,
        )

    repository.mark_all_steps(rollback_run.id, "failed", stdout or stderr)
    rollback_run = repository.finish_run(
        rollback_run.id,
        status="failed",
        error_message=stdout or stderr or "Falha ao aplicar rollback.",
    )
    return UpdateRollbackResponse(
        accepted=False,
        message="Rollback do Printora falhou. Consulte histórico.",
        source_run=source_run,
        rollback_run=rollback_run,
        script_stdout=stdout,
        script_stderr=stderr,
    )


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


def _validate_rollback_confirmation(confirmation_phrase: str) -> None:
    if confirmation_phrase != "ROLLBACK PRINTORA":
        raise ValueError("Confirmação obrigatória inválida.")


def _validate_release_tag(target_tag: str, stable_release_tags: set[str] | None) -> None:
    if not target_tag or not re.fullmatch(r"v[0-9]+[.][0-9]+[.][0-9]+", target_tag):
        raise ValueError("Tag inválida para update.")
    if stable_release_tags is None:
        return
    if target_tag not in stable_release_tags:
        raise ValueError("Tag não pertence às releases estáveis disponíveis.")


def _run_update_script(
    *,
    script_path: Path,
    mode: str,
    target_tag: str,
    source_url: str | None,
    project_root: Path,
    timeout_seconds: float,
    run_id: int | None = None,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

    env = os.environ.copy()
    if source_url:
        env["PRINTORA_UPDATE_REMOTE_URL"] = source_url
    if run_id is not None:
        env["PRINTORA_UPDATE_RUN_ID"] = str(run_id)
    return subprocess.run(
        _update_script_command(script_path=script_path, mode=mode, target_tag=target_tag, extra_args=extra_args),
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
    source_url: str | None,
    project_root: Path,
    run_id: int,
    extra_args: list[str] | None = None,
    log_path: Path | None = None,
) -> None:
    import os

    env = os.environ.copy()
    if source_url:
        env["PRINTORA_UPDATE_REMOTE_URL"] = source_url
    env["PRINTORA_UPDATE_RUN_ID"] = str(run_id)
    log_handle = None
    stdout = subprocess.DEVNULL
    stderr = subprocess.DEVNULL
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("ab")
        stdout = log_handle
        stderr = subprocess.STDOUT
    subprocess.Popen(
        _update_script_command(script_path=script_path, mode=mode, target_tag=target_tag, extra_args=extra_args),
        cwd=str(project_root),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
        close_fds=True,
    )
    if log_handle is not None:
        log_handle.close()


def _detached_update_log_path(database_path: Path, run_id: int) -> Path:
    return database_path.parent / "logs" / f"self-update-run-{run_id}.log"


def _script_path_for_environment(
    environment: UpdateEnvironment,
    *,
    override_script_path: Path | None,
    android_script_path: Path | None,
    unix_script_path: Path | None,
    windows_script_path: Path | None,
) -> Path:
    if override_script_path is not None:
        return override_script_path
    if environment == "android_termux" and android_script_path is not None:
        return android_script_path
    if environment == "unix" and unix_script_path is not None:
        return unix_script_path
    if environment == "windows" and windows_script_path is not None:
        return windows_script_path
    raise ValueError(f"Script de update não configurado para ambiente: {environment}")


def _update_script_command(*, script_path: Path, mode: str, target_tag: str, extra_args: list[str] | None = None) -> list[str]:
    clean_extra_args = extra_args or []
    if script_path.suffix.lower() != ".ps1":
        command = ["bash", str(script_path), mode]
        if mode != "--rollback":
            command.extend(["--tag", target_tag])
        command.extend(clean_extra_args)
        return command
    executable = _powershell_executable()
    powershell_mode = {
        "--plan": "--Plan",
        "--apply": "--Apply",
        "--rollback": "--Rollback",
    }.get(mode, mode)
    command = [
        executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        powershell_mode,
    ]
    if mode != "--rollback":
        command.extend(["-Tag", target_tag])
    command.extend(clean_extra_args)
    return command


def _powershell_executable() -> str:
    import shutil

    return shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe") or "powershell.exe"


def _should_detach_self_update(environment: UpdateEnvironment, project_root: Path) -> bool:
    if sys.platform == "win32":
        return False
    project_path = str(project_root)
    if environment == "android_termux":
        return project_path.startswith("/data/data/com.termux/")
    if environment == "unix":
        return project_path.startswith(("/Users/", "/home/", "/opt/", "/srv/"))
    if environment == "windows":
        return sys.platform == "win32"
    return False


def _rollback_extra_args(source_run_id: int, previous_path: str, db_backup_path: str | None) -> list[str]:
    args = ["--run-id", str(source_run_id), "--previous-path", previous_path]
    if db_backup_path:
        args.extend(["--db-backup", db_backup_path])
    return args


def _require_safe_previous_path(value: str | None, project_root: Path) -> str:
    if value is None:
        raise ValueError("Run não possui pasta anterior para rollback.")
    path = _safe_absolute_path(value, "previous_project_path")
    project_path = project_root.resolve(strict=False)
    if path == project_path:
        raise ValueError("previous_project_path não pode ser a pasta atual do projeto.")
    if not path.name or "previous-update" not in path.name:
        raise ValueError("previous_project_path não parece ser backup de update.")
    if not path.exists():
        raise ValueError(f"previous_project_path não existe: {path}")
    return str(path)


def _safe_optional_db_backup_path(value: str | None, database_path: Path) -> str | None:
    if not value:
        return None
    path = _safe_absolute_path(value, "backup_db_path")
    if "before-update" not in path.name:
        raise ValueError("backup_db_path não parece ser backup de update.")
    if not path.exists():
        raise ValueError(f"backup_db_path não existe: {path}")
    data_path = database_path.resolve(strict=False).parent
    backup_parent = path.parent.resolve(strict=False)
    allowed_parent = (data_path / "backups").resolve(strict=False)
    if backup_parent != allowed_parent:
        raise ValueError("backup_db_path fora da pasta de backups do Printora.")
    return str(path)


def _safe_absolute_path(value: str, label: str) -> Path:
    if not value.strip():
        raise ValueError(f"{label} vazio.")
    raw = Path(value)
    if not raw.is_absolute():
        raise ValueError(f"{label} deve ser absoluto.")
    if ".." in raw.parts:
        raise ValueError(f"{label} contém segmento inseguro.")
    path = raw.resolve(strict=False)
    if path == Path(path.anchor):
        raise ValueError(f"{label} não pode apontar para raiz.")
    return path


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


def _finish_interrupted_run(
    connection: sqlite3.Connection,
    *,
    run_id: int,
    run_status: UpdateRunStatus,
    step_status: UpdateStepStatus,
    message: str,
) -> None:
    connection.execute(
        """
        UPDATE app_update_runs
        SET status = ?,
            finished_at = CURRENT_TIMESTAMP,
            error_message = COALESCE(error_message, ?)
        WHERE id = ? AND status = 'running'
        """,
        (run_status, message, run_id),
    )
    connection.execute(
        """
        UPDATE app_update_steps
        SET status = ?,
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            finished_at = CURRENT_TIMESTAMP,
            log_excerpt = COALESCE(log_excerpt, ?)
        WHERE run_id = ? AND status IN ('pending', 'running')
        """,
        (step_status, message[:4000], run_id),
    )


def _normalize_version(value: str) -> str:
    return value.strip().lower().removeprefix("v")


def _optional_payload_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return str(value) if value else None


def _steps_for_environment(environment: UpdateEnvironment) -> list[tuple[str, str]]:
    android_steps: list[tuple[str, str]] = [
        ("validate_environment", "Validar ambiente, projeto, data dir e tag remota"),
        ("backup_database", "Criar backup obrigatório do printora.db"),
        ("backup_project", "Preservar pasta atual como Printora.previous-update-<timestamp>"),
        ("checkout_release", "Clonar release alvo em Printora.next"),
        ("preserve_venv", "Preservar backend/.venv quando possível"),
        ("install_backend", "Instalar backend editable sem dependências"),
        ("apply_schema", "Inicializar backend para aplicar SQL idempotente"),
        ("build_frontend", "Buildar frontend quando necessário"),
        ("restart_app", "Reiniciar Printora e anúncio printora.local"),
        ("validate_health", "Validar /health"),
    ]
    replace_project_later_steps: list[tuple[str, str]] = [
        ("validate_environment", "Validar ambiente, projeto, data dir e tag remota"),
        ("backup_database", "Criar backup obrigatório do printora.db"),
        ("checkout_release", "Clonar release alvo em Printora.next"),
        ("preserve_venv", "Preservar backend/.venv quando possível"),
        ("install_backend", "Instalar backend editable sem dependências"),
        ("apply_schema", "Inicializar backend para aplicar SQL idempotente"),
        ("build_frontend", "Buildar frontend quando necessário"),
        ("backup_project", "Preservar pasta atual como Printora.previous-update-<timestamp>"),
        ("restart_app", "Reiniciar Printora"),
        ("validate_health", "Validar /health"),
    ]
    if environment == "android_termux":
        return android_steps
    if environment == "windows":
        return [(key, "Reiniciar pelo runner Windows") if key == "restart_app" else (key, title) for key, title in replace_project_later_steps]
    return replace_project_later_steps


def _rollback_steps_for_environment(environment: UpdateEnvironment) -> list[tuple[str, str]]:
    first_step = {
        "android_termux": "Validar Termux, tmux, pasta anterior e backup de banco",
        "unix": "Validar Unix, modo de restart, pasta anterior e backup de banco",
        "windows": "Validar PowerShell, runner Windows, pasta anterior e backup de banco",
        "unknown": "Validar ambiente de rollback",
    }[environment]
    return [
        ("validate_rollback", first_step),
        ("preserve_current", "Preservar pasta atual antes do rollback"),
        ("restore_project", "Restaurar pasta anterior do projeto"),
        ("restore_database", "Restaurar backup de banco quando informado"),
        ("restart_app", "Reiniciar Printora"),
        ("validate_health", "Validar /health após rollback"),
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
