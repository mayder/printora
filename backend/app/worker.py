from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import socket
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4

from app.config import get_settings
from app.modules.platform.durable_execution import DurableExecutionRepository, DurableJob
from app.modules.platform.event_dispatcher import EventDispatcher, EventSubscription
from app.modules.platform.recomposable_redis import RecomposableRedis


JobHandler = Callable[[DurableJob], dict[str, Any]]
LOGGER = logging.getLogger("printora.worker")
SUPPORTED_QUEUES = ("outbox", "critical", "default", "bulk")


@dataclass(frozen=True)
class WorkerOptions:
    queue_name: str
    concurrency: int
    poll_seconds: float
    lease_seconds: int
    release_sha: str


class DurableWorker:
    def __init__(self, options: WorkerOptions, handlers: dict[str, JobHandler]) -> None:
        self.options = options
        self.handlers = handlers
        self.repository = DurableExecutionRepository(get_settings().database_path)
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}:{options.queue_name}:{uuid4().hex[:8]}"
        self.stopping = threading.Event()

    def run(self) -> None:
        self.repository.register_worker(
            self.worker_id,
            self.options.queue_name,
            self.options.release_sha,
            self.options.concurrency,
        )
        self._install_signals()
        futures: set[Future[None]] = set()
        with ThreadPoolExecutor(max_workers=self.options.concurrency, thread_name_prefix="printora-worker") as pool:
            try:
                while not self.stopping.is_set():
                    futures = {future for future in futures if not future.done()}
                    desired = self.repository.worker_desired_state(self.options.queue_name)
                    self.repository.heartbeat_worker(self.worker_id, "paused" if desired == "paused" else "running")
                    if desired in {"paused", "draining"}:
                        if desired == "draining" and not futures:
                            break
                        self.stopping.wait(self.options.poll_seconds)
                        continue
                    while len(futures) < self.options.concurrency and not self.stopping.is_set():
                        job = self.repository.claim_job(
                            self.options.queue_name,
                            self.worker_id,
                            self.options.lease_seconds,
                        )
                        if job is None:
                            break
                        futures.add(pool.submit(self._execute, job))
                    self.stopping.wait(self.options.poll_seconds)
            finally:
                self.repository.heartbeat_worker(self.worker_id, "draining")
                for future in futures:
                    future.result()
                self.repository.stop_worker(self.worker_id)

    def _execute(self, job: DurableJob) -> None:
        handler = self.handlers.get(job.job_type)
        if handler is None:
            self.repository.retry_job(job.id, job.lease_token or "", "handler não registrado", _backoff(job.attempts))
            _log("job_retry", job=job, reason="handler_missing")
            return
        heartbeat_stop = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_lease,
            args=(job, heartbeat_stop),
            name=f"lease-{job.id}",
            daemon=True,
        )
        heartbeat.start()
        try:
            result = handler(job)
            if self.repository.complete_job(job.id, job.lease_token or "", result) is None:
                _log("job_stale_completion", job=job)
                return
            _log("job_succeeded", job=job)
        except Exception as exc:
            self.repository.retry_job(job.id, job.lease_token or "", str(exc), _backoff(job.attempts))
            _log("job_retry", job=job, reason=type(exc).__name__)
        finally:
            heartbeat_stop.set()
            heartbeat.join(timeout=1)

    def _heartbeat_lease(self, job: DurableJob, stopped: threading.Event) -> None:
        interval = max(2, self.options.lease_seconds // 3)
        while not stopped.wait(interval):
            if not self.repository.heartbeat_job(job.id, job.lease_token or "", self.options.lease_seconds):
                return

    def _install_signals(self) -> None:
        def stop(_signum, _frame) -> None:
            self.stopping.set()

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)


class OutboxWorker:
    def __init__(self, options: WorkerOptions) -> None:
        self.options = options
        self.repository = DurableExecutionRepository(get_settings().database_path)
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}:outbox:{uuid4().hex[:8]}"
        self.stopping = threading.Event()
        self.dispatcher = EventDispatcher(
            get_settings().database_path,
            self.worker_id,
            {
                "agent.job.created": (
                    EventSubscription(
                        consumer_name="agent-realtime-v1",
                        queue_name="critical",
                        job_type="realtime.agent_job_available",
                        priority=10,
                    ),
                ),
                "search.source.changed": (
                    EventSubscription(
                        consumer_name="search-index-v1",
                        queue_name="bulk",
                        job_type="search.rebuild",
                        priority=80,
                    ),
                ),
                "moderation.report.created": (
                    EventSubscription(
                        consumer_name="analytics-moderation-v1",
                        queue_name="bulk",
                        job_type="analytics.ingest_event",
                        priority=90,
                    ),
                ),
            },
        )

    def run(self) -> None:
        self.repository.register_worker(self.worker_id, "outbox", self.options.release_sha, 1)
        self._install_signals()
        try:
            while not self.stopping.is_set():
                desired = self.repository.worker_desired_state("outbox")
                self.repository.heartbeat_worker(self.worker_id, "paused" if desired == "paused" else "running")
                if desired == "draining":
                    break
                if desired == "paused":
                    self.stopping.wait(self.options.poll_seconds)
                    continue
                result = self.dispatcher.dispatch_once()
                if result.status == "idle":
                    self.stopping.wait(self.options.poll_seconds)
        finally:
            self.repository.stop_worker(self.worker_id)

    def _install_signals(self) -> None:
        def stop(_signum, _frame) -> None:
            self.stopping.set()

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)


def _realtime_notification(job: DurableJob) -> dict[str, Any]:
    settings = get_settings()
    redis_service = RecomposableRedis(settings.redis_url, settings.redis_prefix, settings.redis_timeout_seconds)
    payload = job.payload.get("payload") or {}
    notified = redis_service.publish(
        "agent",
        {
            "type": "job_available",
            "agent_job_id": payload.get("job_id"),
            "printer_id": payload.get("printer_id"),
            "agent_id": payload.get("agent_id"),
            "event_id": job.payload.get("event_id"),
        },
    )
    return {
        "status": "durable",
        "delivery": "pubsub" if notified else "polling_resume",
        "event_id": job.payload.get("event_id"),
    }


def _execute_slicing(job: DurableJob) -> dict[str, Any]:
    from app.slicing_pipeline import SlicingPipelineRepository

    settings = get_settings()
    slicing_job = SlicingPipelineRepository(settings.database_path, settings).run_job(
        int(job.payload["slicing_job_id"]),
        int(job.payload["actor_user_id"]) if job.payload.get("actor_user_id") is not None else None,
    )
    return {"slicing_job_id": slicing_job.id, "status": slicing_job.status}


def _rebuild_search(_job: DurableJob) -> dict[str, Any]:
    from app.search_discovery import SearchDiscoveryRepository

    settings = get_settings()
    indexed_count = SearchDiscoveryRepository(settings.database_path).rebuild_index()
    return {"indexed_count": indexed_count, "materialization": "search_documents"}


def _ingest_analytics_event(job: DurableJob) -> dict[str, Any]:
    from app.modules.administration.intelligence import IntelligenceRepository
    from app.modules.administration.intelligence_contracts import SanitizedEventCreate

    settings = get_settings()
    event_type = str(job.payload["event_type"])
    payload = SanitizedEventCreate(
        event_id=str(job.payload["event_id"]),
        event_type=event_type,
        schema_version=int(job.payload.get("schema_version", 1)),
        purpose="safety_moderation",
        occurred_at=str(job.available_at),
        payload=dict(job.payload.get("payload") or {}),
    )
    result = IntelligenceRepository(settings.database_path).ingest(payload)
    return {"event_id": result["event_id"], "status": result["status"]}


def _handlers() -> dict[str, JobHandler]:
    return {
        "realtime.agent_job_available": _realtime_notification,
        "slicing.execute": _execute_slicing,
        "search.rebuild": _rebuild_search,
        "analytics.ingest_event": _ingest_analytics_event,
    }


def _backoff(attempt: int) -> int:
    return min(300, 2 ** max(0, min(attempt, 8)))


def _log(event: str, *, job: DurableJob, reason: str | None = None) -> None:
    LOGGER.info(
        json.dumps(
            {
                "event": event,
                "job_id": job.id,
                "job_type": job.job_type,
                "queue": job.queue_name,
                "attempt": job.attempts,
                "reason": reason,
            },
            sort_keys=True,
        )
    )


def _parse_options() -> WorkerOptions:
    parser = argparse.ArgumentParser(description="Printora durable worker")
    parser.add_argument("--queue", required=True, choices=SUPPORTED_QUEUES)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--lease-seconds", type=int, default=45)
    args = parser.parse_args()
    return WorkerOptions(
        queue_name=args.queue,
        concurrency=max(1, min(args.concurrency, 16)),
        poll_seconds=max(0.1, min(args.poll_seconds, 10.0)),
        lease_seconds=max(10, min(args.lease_seconds, 300)),
        release_sha=os.environ.get("PRINTORA_RELEASE_SHA", "development")[:64],
    )


def main() -> None:
    logging.basicConfig(level=os.environ.get("PRINTORA_LOG_LEVEL", "INFO"))
    options = _parse_options()
    if options.queue_name == "outbox":
        OutboxWorker(options).run()
        return
    DurableWorker(options, _handlers()).run()


if __name__ == "__main__":
    main()
