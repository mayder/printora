from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.database import connect_database
from app.modules.platform.durable_execution import (
    DurableExecutionRepository,
    OutboxEvent,
)


PayloadFactory = Callable[[OutboxEvent], dict[str, Any]]


@dataclass(frozen=True)
class EventSubscription:
    consumer_name: str
    queue_name: str
    job_type: str
    payload_factory: PayloadFactory = lambda event: {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "schema_version": event.schema_version,
        "payload": event.payload,
        "headers": event.headers,
    }
    priority: int = 100
    max_attempts: int = 8


@dataclass(frozen=True)
class DispatchResult:
    status: str
    event_id: str | None = None
    jobs_created: int = 0


class EventDispatcher:
    def __init__(
        self,
        database_path: Path,
        dispatcher_id: str,
        subscriptions: dict[str, tuple[EventSubscription, ...]],
    ) -> None:
        self.database_path = database_path
        self.dispatcher_id = dispatcher_id
        self.subscriptions = subscriptions
        self.repository = DurableExecutionRepository(database_path)

    def dispatch_once(self) -> DispatchResult:
        event = self.repository.claim_event(self.dispatcher_id)
        if event is None:
            return DispatchResult(status="idle")
        try:
            count = self._materialize_subscriptions(event)
        except Exception as exc:
            delay = min(300, 2 ** min(event.attempts, 8))
            self.repository.retry_event(event.id, event.lease_token or "", str(exc), delay)
            return DispatchResult(status="retry", event_id=event.event_id)
        return DispatchResult(status="published", event_id=event.event_id, jobs_created=count)

    def _materialize_subscriptions(self, event: OutboxEvent) -> int:
        subscriptions = self.subscriptions.get(event.event_type, ())
        with connect_database(self.database_path) as connection:
            for subscription in subscriptions:
                self.repository.enqueue_job(
                    job_key=f"event:{event.event_id}:{subscription.consumer_name}",
                    queue_name=subscription.queue_name,
                    job_type=subscription.job_type,
                    payload=subscription.payload_factory(event),
                    schema_version=event.schema_version,
                    ordering_key=event.ordering_key,
                    owner_type=event.headers.get("owner_type"),
                    owner_id=event.headers.get("owner_id"),
                    priority=subscription.priority,
                    max_attempts=subscription.max_attempts,
                    connection=connection,
                )
            if not self.repository.publish_event(event.id, event.lease_token or "", connection=connection):
                raise RuntimeError("lease do evento expirou durante o dispatch")
        return len(subscriptions)
