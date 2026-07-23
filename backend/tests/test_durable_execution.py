from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.modules.platform.durable_execution import (
    DurableExecutionRepository,
    EventEnvelope,
)
from app.modules.platform.event_dispatcher import EventDispatcher, EventSubscription
from app.modules.platform import durable_execution


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
    assert repository.complete_job(first.id, first.lease_token or "", {"worker": "stale"}) is None


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


def test_outbox_preserves_order_and_dispatch_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    second = EventEnvelope(**{**_event("evt-2").__dict__, "sequence_no": 2})
    with connect_database(database_path) as connection:
        repository.append_event(connection, _event())
        repository.append_event(connection, second)

    dispatcher = EventDispatcher(
        database_path,
        "dispatcher-a",
        {
            "printer.job_requested": (
                EventSubscription("agent-realtime", "critical", "realtime.agent_job_available", priority=10),
            )
        },
    )

    first_result = dispatcher.dispatch_once()
    second_result = dispatcher.dispatch_once()
    assert first_result.event_id == "evt-1"
    assert second_result.event_id == "evt-2"
    assert dispatcher.dispatch_once().status == "idle"
    with connect_database(database_path) as connection:
        jobs = connection.execute("SELECT job_key FROM durable_jobs ORDER BY id").fetchall()
        events = connection.execute("SELECT status FROM outbox_events ORDER BY sequence_no").fetchall()
    assert [row["job_key"] for row in jobs] == [
        "event:evt-1:agent-realtime",
        "event:evt-2:agent-realtime",
    ]
    assert [row["status"] for row in events] == ["published", "published"]


def test_dispatch_retry_does_not_duplicate_materialized_job(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    with connect_database(database_path) as connection:
        repository.append_event(connection, _event())

    dispatcher = EventDispatcher(
        database_path,
        "dispatcher-a",
        {"printer.job_requested": (EventSubscription("consumer", "default", "consume"),)},
    )
    original_publish = repository.publish_event
    calls = 0

    def fail_first_publish(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("process stopped before commit")
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(dispatcher.repository, "publish_event", fail_first_publish)
    assert dispatcher.dispatch_once().status == "retry"
    with connect_database(database_path) as connection:
        connection.execute("UPDATE outbox_events SET available_at = '2000-01-01 00:00:00'")
    assert dispatcher.dispatch_once().status == "published"
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) AS total FROM durable_jobs").fetchone()["total"] == 1


def test_queue_quota_applies_backpressure_without_affecting_other_class(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    monkeypatch.setitem(durable_execution.QUEUE_ACTIVE_LIMITS, "bulk", 1)
    repository.enqueue_job(job_key="bulk-1", queue_name="bulk", job_type="test", payload={})

    with pytest.raises(durable_execution.QueueSaturatedError):
        repository.enqueue_job(job_key="bulk-2", queue_name="bulk", job_type="test", payload={})

    critical = repository.enqueue_job(job_key="critical-1", queue_name="critical", job_type="test", payload={})
    assert critical.status == "queued"


def test_dead_letter_replay_requires_exact_confirmation_and_emits_audit_event(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = DurableExecutionRepository(database_path)
    repository.enqueue_job(
        job_key="dead-letter-1",
        queue_name="default",
        job_type="test",
        payload={},
        max_attempts=1,
    )
    claimed = repository.claim_job("default", "worker-a")
    assert claimed is not None
    repository.retry_job(claimed.id, claimed.lease_token or "", "controlled", 1)

    assert repository.dead_letter_preview("default")[0]["job_key"] == "dead-letter-1"
    with pytest.raises(ValueError, match="não confere"):
        repository.replay_dead_letter(claimed.id, "wrong", "replay-001", "admin")
    replayed = repository.replay_dead_letter(claimed.id, "dead-letter-1", "replay-001", "admin", "default")

    assert replayed.status == "queued"
    with connect_database(database_path) as connection:
        event = connection.execute(
            "SELECT event_type, headers_json FROM outbox_events WHERE event_id = 'job-replay:replay-001'"
        ).fetchone()
    assert event["event_type"] == "platform.job.replayed"
    assert '"actor":"admin"' in event["headers_json"]
