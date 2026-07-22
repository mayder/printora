from pathlib import Path

from app.config import get_settings
from app.database import connect_database, initialize_database
from app.modules.platform.durable_execution import DurableExecutionRepository
from app.worker import DurableWorker, WorkerOptions


def _configure(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    return database_path


def test_worker_completes_claimed_job_once(tmp_path: Path, monkeypatch) -> None:
    database_path = _configure(tmp_path, monkeypatch)
    repository = DurableExecutionRepository(database_path)
    repository.enqueue_job(job_key="worker-success", queue_name="default", job_type="test.ok", payload={"value": 7})
    claimed = repository.claim_job("default", "worker-test")
    assert claimed is not None
    worker = DurableWorker(
        WorkerOptions("default", 1, 0.1, 10, "test-release"),
        {"test.ok": lambda job: {"received": job.payload["value"]}},
    )

    worker._execute(claimed)

    with connect_database(database_path) as connection:
        row = connection.execute("SELECT status, result_json FROM durable_jobs WHERE id = ?", (claimed.id,)).fetchone()
    assert row["status"] == "succeeded"
    assert '"received":7' in row["result_json"]
    get_settings.cache_clear()


def test_worker_failure_is_requeued_with_backoff(tmp_path: Path, monkeypatch) -> None:
    database_path = _configure(tmp_path, monkeypatch)
    repository = DurableExecutionRepository(database_path)
    repository.enqueue_job(job_key="worker-retry", queue_name="critical", job_type="test.fail", payload={})
    claimed = repository.claim_job("critical", "worker-test")
    assert claimed is not None
    worker = DurableWorker(
        WorkerOptions("critical", 1, 0.1, 10, "test-release"),
        {"test.fail": lambda _job: (_ for _ in ()).throw(RuntimeError("controlled"))},
    )

    worker._execute(claimed)

    with connect_database(database_path) as connection:
        row = connection.execute("SELECT status, attempts, error_message FROM durable_jobs WHERE id = ?", (claimed.id,)).fetchone()
    assert row["status"] == "queued"
    assert row["attempts"] == 1
    assert row["error_message"] == "controlled"
    get_settings.cache_clear()


def test_worker_control_and_instance_state_are_persisted(tmp_path: Path, monkeypatch) -> None:
    database_path = _configure(tmp_path, monkeypatch)
    repository = DurableExecutionRepository(database_path)

    assert repository.worker_desired_state("bulk") == "running"
    repository.register_worker("worker-1", "bulk", "release-a", 1)
    repository.heartbeat_worker("worker-1", "draining")
    repository.stop_worker("worker-1")

    with connect_database(database_path) as connection:
        row = connection.execute("SELECT state, release_sha, stopped_at FROM worker_instances WHERE worker_id = ?", ("worker-1",)).fetchone()
    assert row["state"] == "stopped"
    assert row["release_sha"] == "release-a"
    assert row["stopped_at"] is not None
    get_settings.cache_clear()
