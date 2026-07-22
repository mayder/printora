from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.modules.platform.durable_execution import (
    DurableExecutionRepository,
    EventEnvelope,
)


def _event(event_id: str = "evt-1") -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        aggregate_type="printer",
        aggregate_id="7",
        event_type="printer.job_requested",
        ordering_key="printer:7",
        sequence_no=1,
        payload={"job_id": 42},
    )


def test_business_change_and_outbox_are_atomic(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)

    with pytest.raises(RuntimeError):
        with connect_database(database_path) as connection:
            connection.execute("CREATE TABLE atomic_probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO atomic_probe (id, value) VALUES (?, ?)", (1, "changed"))
            repository.append_event(connection, _event())
            raise RuntimeError("rollback")

    with connect_database(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) AS total FROM outbox_events").fetchone()["total"] == 0


def test_job_key_is_idempotent_and_divergence_is_rejected(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)

    first = repository.enqueue_job(job_key="job-1", queue_name="critical", job_type="agent.notify", payload={"id": 7})
    repeated = repository.enqueue_job(job_key="job-1", queue_name="critical", job_type="agent.notify", payload={"id": 7})

    assert repeated.id == first.id
    with pytest.raises(ValueError, match="contrato divergente"):
        repository.enqueue_job(job_key="job-1", queue_name="critical", job_type="agent.notify", payload={"id": 8})


def test_expired_lease_is_recovered_without_two_effective_completions(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    repository.enqueue_job(job_key="job-lease", queue_name="default", job_type="test", payload={})

    first = repository.claim_job("default", "worker-a", lease_seconds=5)
    assert first is not None and first.attempts == 1
    with connect_database(database_path) as connection:
        connection.execute(
            "UPDATE durable_jobs SET lease_expires_at = '2000-01-01 00:00:00' WHERE id = ?",
            (first.id,),
        )

    recovered = repository.claim_job("default", "worker-b", lease_seconds=5)
    assert recovered is not None and recovered.id == first.id and recovered.attempts == 2
    assert repository.complete_job(first.id, first.lease_token or "", {"worker": "a"}) is None
    completed = repository.complete_job(recovered.id, recovered.lease_token or "", {"worker": "b"})
    assert completed is not None and completed.status == "succeeded"


def test_retry_reaches_dead_letter_at_attempt_limit(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    repository.enqueue_job(
        job_key="job-dlq",
        queue_name="bulk",
        job_type="test",
        payload={},
        max_attempts=1,
    )

    claimed = repository.claim_job("bulk", "worker-a")
    assert claimed is not None
    failed = repository.retry_job(claimed.id, claimed.lease_token or "", "temporary failure", 1)

    assert failed is not None and failed.status == "dead_letter"
    assert repository.claim_job("bulk", "worker-b") is None


def test_inbox_deduplicates_same_event_and_rejects_changed_payload(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)

    accepted = repository.begin_inbox("search-index", _event())
    repeated = repository.begin_inbox("search-index", _event())

    assert accepted.accepted is True
    assert repeated.duplicate is True
    assert repository.finish_inbox("search-index", "evt-1", {"indexed": True}) is True
    changed = EventEnvelope(**{**_event().__dict__, "payload": {"job_id": 99}})
    with pytest.raises(ValueError, match="payload divergente"):
        repository.begin_inbox("search-index", changed)
