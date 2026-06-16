import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

import app.self_update as self_update_module
from app.config import get_settings
from app.database import initialize_database
from app.main import app
from app.self_update import SelfUpdateRepository, UpdatePlanRequest, build_update_plan


def test_create_android_termux_plan(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)

    response = build_update_plan(
        repository=repository,
        request=UpdatePlanRequest(target_tag="v0.1.1", source_url="https://github.com/mayder/printora"),
        project_root=tmp_path / "Printora",
        environment="android_termux",
    )

    assert response.safe_mode == "plan_only"
    assert response.update_supported is True
    assert response.can_apply is True
    assert response.run.target_version == "0.1.1"
    assert response.run.environment == "android_termux"
    assert response.run.status == "planned"
    assert [step.step_key for step in response.run.steps] == [
        "validate_environment",
        "backup_database",
        "backup_project",
        "checkout_release",
        "preserve_venv",
        "install_backend",
        "apply_schema",
        "build_frontend",
        "restart_app",
        "validate_health",
    ]


def test_create_unix_plan(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)

    response = build_update_plan(
        repository=repository,
        request=UpdatePlanRequest(target_tag="v0.1.2"),
        project_root=tmp_path / "Printora",
        environment="unix",
    )

    assert response.update_supported is True
    assert response.can_apply is True
    assert response.run.environment == "unix"
    assert response.run.steps[0].step_key == "validate_environment"
    assert response.run.steps[-1].step_key == "validate_health"


def test_create_windows_plan(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)

    response = build_update_plan(
        repository=repository,
        request=UpdatePlanRequest(target_tag="v0.1.2"),
        project_root=tmp_path / "Printora",
        environment="windows",
    )

    assert response.update_supported is True
    assert response.can_apply is True
    assert response.run.environment == "windows"
    assert response.run.steps[0].step_key == "validate_environment"
    assert response.run.steps[-1].step_key == "validate_health"


def test_plan_rejects_unknown_environment(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)

    try:
        build_update_plan(
            repository=repository,
            request=UpdatePlanRequest(target_tag="v0.1.1"),
            project_root=tmp_path,
            environment="unknown",
        )
    except ValueError as exc:
        assert "Ambiente não suportado" in str(exc)
    else:
        raise AssertionError("unknown environment should be rejected")


def test_update_history_lists_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            plan_response = client.post(
                "/api/system/update/plan",
                json={"target_tag": "v0.1.1", "source_url": "https://github.com/mayder/printora"},
            )
            history_response = client.get("/api/system/update/history")
            run_response = client.get(f"/api/system/update/runs/{plan_response.json()['run']['id']}")

        assert plan_response.status_code == 200
        assert history_response.status_code == 200
        assert run_response.status_code == 200
        history = history_response.json()
        run = run_response.json()
        assert len(history["runs"]) == 1
        assert history["runs"][0]["target_tag"] == "v0.1.1"
        assert history["runs"][0]["steps"]
        assert run["target_version"] == "0.1.1"
        assert run["environment"] == "android_termux"
    finally:
        get_settings.cache_clear()


def test_reconcile_running_update_succeeds_when_installed_version_matches(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)
    run = repository.create_run(
        target_tag="v0.1.9",
        source_url=None,
        environment="unix",
        current_project_path=str(tmp_path / "Printora"),
        status="running",
        steps=[("install_backend", "Instalar backend editable sem dependências")],
    )

    reconciled = repository.reconcile_interrupted_updates(installed_version="0.1.9")
    updated = repository.get_run(run.id)

    assert reconciled == 1
    assert updated is not None
    assert updated.status == "succeeded"
    assert updated.finished_at is not None
    assert "versao instalada 0.1.9 ja corresponde" in (updated.error_message or "")
    assert updated.steps[0].status == "skipped"


def test_reconcile_running_update_fails_only_when_stale_and_version_mismatches(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)
    run = repository.create_run(
        target_tag="v0.2.0",
        source_url=None,
        environment="unix",
        current_project_path=str(tmp_path / "Printora"),
        status="running",
        steps=[("install_backend", "Instalar backend editable sem dependências")],
    )

    assert repository.reconcile_interrupted_updates(installed_version="0.1.9") == 0
    assert repository.get_run(run.id).status == "running"  # type: ignore[union-attr]

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE app_update_runs SET started_at = datetime('now', '-45 minutes') WHERE id = ?",
            (run.id,),
        )

    reconciled = repository.reconcile_interrupted_updates(installed_version="0.1.9")
    updated = repository.get_run(run.id)

    assert reconciled == 1
    assert updated is not None
    assert updated.status == "failed"
    assert "ficou orfao" in (updated.error_message or "")
    assert updated.steps[0].status == "failed"


def test_plan_endpoint_rejects_unknown_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "unknown")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.post("/api/system/update/plan", json={"target_tag": "v0.1.1"})

        assert response.status_code == 400
        assert "Ambiente não suportado" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_reconcile_endpoint_marks_stale_running_update_failed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        database_path = tmp_path / "printora.db"
        initialize_database(database_path)
        repository = SelfUpdateRepository(database_path)
        run = repository.create_run(
            target_tag="v9.9.9",
            source_url=None,
            environment="unix",
            current_project_path=str(tmp_path / "Printora"),
            status="running",
            steps=[("install_backend", "Instalar backend editable sem dependências")],
        )
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                "UPDATE app_update_runs SET started_at = datetime('now', '-5 minutes') WHERE id = ?",
                (run.id,),
            )

        with TestClient(app) as client:
            response = client.post("/api/system/update/reconcile")

        assert response.status_code == 200
        payload = response.json()
        assert payload["reconciled"] == 1
        assert payload["running_updates"] == 0
        assert payload["runs"][0]["status"] == "failed"
    finally:
        get_settings.cache_clear()


def test_schema_versioning_includes_app_update_sql(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        scripts = [
            row[0]
            for row in connection.execute(
                "SELECT script_name FROM schema_versions ORDER BY execution_order"
            ).fetchall()
        ]
        run_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'app_update_runs'"
        ).fetchone()
        step_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'app_update_steps'"
        ).fetchone()

    assert scripts[-1] == "059_social_safety_antiabuse.sql"
    assert run_table == ("app_update_runs",)
    assert step_table == ("app_update_steps",)


def test_apply_rejects_without_confirmation(tmp_path: Path, monkeypatch) -> None:
    _configure_fixture_releases(tmp_path, monkeypatch)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={"target_tag": "v0.2.0", "confirmation_phrase": "ERRADO"},
            )

        assert response.status_code == 400
        assert "Confirmação obrigatória" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_apply_rejects_invalid_tag(tmp_path: Path, monkeypatch) -> None:
    _configure_fixture_releases(tmp_path, monkeypatch)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={"target_tag": "main", "confirmation_phrase": "ATUALIZAR PRINTORA"},
            )

        assert response.status_code == 400
        assert "Tag inválida" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_apply_allows_strict_stable_tag_when_release_lookup_unavailable(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    _configure_disabled_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "unix")
    monkeypatch.setattr(self_update_module, "_should_detach_self_update", lambda environment, project_root: False)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={"target_tag": "v0.2.0", "confirmation_phrase": "ATUALIZAR PRINTORA"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["accepted"] is True
        assert payload["run"]["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_apply_rejects_unsupported_environment(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "unknown")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={
                    "target_tag": "v0.2.0",
                    "source_url": "https://github.com/mayder/printora/releases/tag/v0.2.0",
                    "confirmation_phrase": "ATUALIZAR PRINTORA",
                },
            )

        assert response.status_code == 400
        assert "not_supported" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_apply_calls_mocked_unix_script_and_persists_success(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "unix")
    monkeypatch.setattr(self_update_module, "_should_detach_self_update", lambda environment, project_root: False)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={
                    "target_tag": "v0.2.0",
                    "source_url": "https://github.com/mayder/printora/releases/tag/v0.2.0",
                    "confirmation_phrase": "ATUALIZAR PRINTORA",
                },
            )
            history_response = client.get("/api/system/update/history")

        assert response.status_code == 200
        payload = response.json()
        history = history_response.json()
        assert payload["accepted"] is True
        assert payload["run"]["environment"] == "unix"
        assert payload["run"]["status"] == "succeeded"
        assert history["runs"][0]["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_apply_calls_mocked_windows_script_and_persists_success(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "windows")
    monkeypatch.setattr(self_update_module, "_should_detach_self_update", lambda environment, project_root: False)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={
                    "target_tag": "v0.2.0",
                    "source_url": "https://github.com/mayder/printora/releases/tag/v0.2.0",
                    "confirmation_phrase": "ATUALIZAR PRINTORA",
                },
            )
            history_response = client.get("/api/system/update/history")

        assert response.status_code == 200
        payload = response.json()
        history = history_response.json()
        assert payload["accepted"] is True
        assert payload["run"]["environment"] == "windows"
        assert payload["run"]["status"] == "succeeded"
        assert history["runs"][0]["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_apply_calls_mocked_android_script_and_persists_success(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={"target_tag": "v0.2.0", "confirmation_phrase": "ATUALIZAR PRINTORA"},
            )
            history_response = client.get("/api/system/update/history")

        assert response.status_code == 200
        payload = response.json()
        history = history_response.json()
        assert payload["accepted"] is True
        assert payload["run"]["status"] == "succeeded"
        assert payload["run"]["backup_db_path"] == "/tmp/printora.db.before-update"
        assert payload["run"]["previous_project_path"] == "/tmp/Printora.previous"
        assert all(step["status"] == "succeeded" for step in payload["run"]["steps"])
        assert history["runs"][0]["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_apply_passes_release_url_to_script_env(tmp_path: Path, monkeypatch) -> None:
    script = _write_env_check_update_script(tmp_path)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    monkeypatch.setattr(self_update_module, "_should_detach_self_update", lambda environment, project_root: False)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={
                    "target_tag": "v0.2.0",
                    "source_url": "https://github.com/mayder/printora/releases/tag/v0.2.0",
                    "confirmation_phrase": "ATUALIZAR PRINTORA",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["accepted"] is True
        assert payload["run"]["status"] == "succeeded"
    finally:
        get_settings.cache_clear()


def test_apply_persists_failure_in_history(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=7)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "detect_update_environment", lambda: "android_termux")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/apply",
                json={"target_tag": "v0.2.0", "confirmation_phrase": "ATUALIZAR PRINTORA"},
            )
            history_response = client.get("/api/system/update/history")

        assert response.status_code == 200
        payload = response.json()
        history = history_response.json()
        assert payload["accepted"] is False
        assert payload["run"]["status"] == "failed"
        assert "mock failure" in payload["run"]["error_message"]
        assert history["runs"][0]["status"] == "failed"
        assert all(step["status"] == "failed" for step in payload["run"]["steps"])
    finally:
        get_settings.cache_clear()


def test_rollback_rejects_without_confirmation(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    run_id = _create_successful_update_run(tmp_path)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/rollback",
                json={"run_id": run_id, "confirmation_phrase": "ERRADO"},
            )

        assert response.status_code == 400
        assert "Confirmação obrigatória" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_rollback_rejects_unsafe_paths(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = SelfUpdateRepository(database_path)
    run = repository.create_run(
        target_tag="v0.2.0",
        source_url=None,
        environment="unix",
        current_project_path=str(tmp_path / "Printora"),
        status="succeeded",
        steps=[("done", "done")],
    )
    repository.finish_run(
        run.id,
        status="succeeded",
        previous_project_path=str(tmp_path / "Printora"),
        backup_db_path=str(tmp_path / "backups" / "printora.db.before-update-unsafe"),
    )
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/rollback",
                json={"run_id": run.id, "confirmation_phrase": "ROLLBACK PRINTORA"},
            )

        assert response.status_code == 400
        assert "previous_project_path" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_rollback_marks_source_run_and_creates_audit_run(tmp_path: Path, monkeypatch) -> None:
    script = _write_mock_update_script(tmp_path, exit_code=0)
    run_id = _create_successful_update_run(tmp_path)
    _configure_fixture_releases(tmp_path, monkeypatch, script)
    monkeypatch.setattr(self_update_module, "_should_detach_self_update", lambda environment, project_root: False)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/system/update/rollback",
                json={"run_id": run_id, "confirmation_phrase": "ROLLBACK PRINTORA"},
            )
            history_response = client.get("/api/system/update/history")

        assert response.status_code == 200
        payload = response.json()
        history = history_response.json()
        assert payload["accepted"] is True
        assert payload["source_run"]["status"] == "rolled_back"
        assert payload["rollback_run"]["status"] == "succeeded"
        assert history["runs"][0]["status"] == "succeeded"
        assert any(run["status"] == "rolled_back" for run in history["runs"])
    finally:
        get_settings.cache_clear()


def _configure_fixture_releases(tmp_path: Path, monkeypatch, script_path: Path | None = None) -> None:
    fixture = Path(__file__).parent / "fixtures" / "github_releases.json"
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RELEASE_SOURCE_MODE", "fixture")
    monkeypatch.setenv("PRINTORA_RELEASE_FIXTURE_PATH", str(fixture))
    if script_path is not None:
        monkeypatch.setenv("PRINTORA_SELF_UPDATE_SCRIPT_PATH", str(script_path))
    get_settings.cache_clear()


def _configure_disabled_releases(tmp_path: Path, monkeypatch, script_path: Path | None = None) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RELEASE_SOURCE_MODE", "disabled")
    if script_path is not None:
        monkeypatch.setenv("PRINTORA_SELF_UPDATE_SCRIPT_PATH", str(script_path))
    get_settings.cache_clear()


def _create_successful_update_run(tmp_path: Path) -> int:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    previous_path = tmp_path / "Printora.previous-update-20260523T011445Z"
    previous_path.mkdir()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup_path = backup_dir / "printora.db.before-update-20260523T011445Z"
    backup_path.write_text("backup", encoding="utf-8")
    repository = SelfUpdateRepository(database_path)
    run = repository.create_run(
        target_tag="v0.2.0",
        source_url=None,
        environment="unix",
        current_project_path=str(tmp_path / "Printora"),
        status="succeeded",
        steps=[("done", "done")],
    )
    repository.finish_run(
        run.id,
        status="succeeded",
        previous_project_path=str(previous_path),
        backup_project_path=str(previous_path),
        backup_db_path=str(backup_path),
    )
    return run.id


def _write_mock_update_script(tmp_path: Path, *, exit_code: int) -> Path:
    script = tmp_path / "android_update_printora.sh"
    if exit_code == 0:
        body = """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "--plan" ]]; then
  echo '{"status":"planned","steps":[{"key":"validate_environment"}]}'
  exit 0
fi
echo '{"status":"succeeded","backup_db_path":"/tmp/printora.db.before-update","previous_project_path":"/tmp/Printora.previous","current_project_path":"/tmp/Printora"}'
"""
    else:
        body = """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "--plan" ]]; then
  echo '{"status":"planned","steps":[{"key":"validate_environment"}]}'
  exit 0
fi
echo '{"status":"failed","error":"mock failure"}'
exit 7
"""
    script.write_text(body, encoding="utf-8")
    script.chmod(0o755)
    return script


def _write_env_check_update_script(tmp_path: Path) -> Path:
    script = tmp_path / "android_update_printora.sh"
    script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${PRINTORA_UPDATE_REMOTE_URL:-}" != "https://github.com/mayder/printora/releases/tag/v0.2.0" ]]; then
  echo '{"status":"failed","error":"missing remote env"}'
  exit 9
fi
if [[ "$1" == "--plan" ]]; then
  echo '{"status":"planned","steps":[{"key":"validate_environment"}]}'
  exit 0
fi
echo '{"status":"succeeded","backup_db_path":"/tmp/printora.db.before-update","previous_project_path":"/tmp/Printora.previous","current_project_path":"/tmp/Printora"}'
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script
