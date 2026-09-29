from __future__ import annotations

from app.config import Settings
from app.modules.operations.reconstruction.adapters import (
    ReconstructionCancelledError,
    ReconstructionUnavailableError,
    build_reconstruction_adapter,
)
from app.modules.operations.reconstruction.repository import ReconstructionRepository
from app.modules.platform.durable_execution import DurableJob


def execute_reconstruction_job(job: DurableJob, settings: Settings) -> dict[str, object]:
    reconstruction_job_id = int(job.payload["reconstruction_job_id"])
    repository = ReconstructionRepository(settings.database_path, settings)
    adapter = build_reconstruction_adapter(
        settings,
        repository.engine_policy_for_worker(reconstruction_job_id),
    )
    attempt_id: int | None = None
    try:
        repository.ensure_engine_available(adapter.engine_key)
        attempt_id, request = repository.begin_attempt(
            reconstruction_job_id,
            adapter.engine_key,
            adapter.adapter_version,
        )
        repository.update_stage(reconstruction_job_id, attempt_id, "camera_poses")
        result = adapter.reconstruct(
            request,
            repository.storage.storage,
            lambda: repository.is_cancel_requested(reconstruction_job_id, attempt_id),
        )
        repository.update_stage(reconstruction_job_id, attempt_id, "packaging")
        completed = repository.succeed(reconstruction_job_id, attempt_id, result)
        try:
            repository.record_engine_success(adapter.engine_key)
        except Exception:
            pass
        return {
            "reconstruction_job_id": completed.id,
            "status": completed.status,
            "artifact_sha256": completed.artifacts[0].sha256 if completed.artifacts else None,
        }
    except ReconstructionCancelledError:
        repository.cancel_from_worker(reconstruction_job_id, attempt_id)
        return {"reconstruction_job_id": reconstruction_job_id, "status": "cancelled"}
    except ReconstructionUnavailableError as exc:
        repository.fail(
            reconstruction_job_id,
            attempt_id,
            retryable=False,
            code="engine_unavailable",
            message=str(exc),
        )
        return {"reconstruction_job_id": reconstruction_job_id, "status": "failed", "error_code": "engine_unavailable"}
    except Exception as exc:
        try:
            repository.record_engine_failure(adapter.engine_key)
        except Exception:
            pass
        retryable = adapter.automatic_retry_safe and job.attempts < job.max_attempts
        repository.fail(
            reconstruction_job_id,
            attempt_id,
            retryable=retryable,
            code="processing_failed",
            message=(
                "Não foi possível reconstruir este conjunto. Tentaremos novamente."
                if retryable
                else "Não foi possível reconstruir este conjunto. Refaça as fotos ou escolha outro modo."
            ),
        )
        raise RuntimeError("reconstruction processing failed") from exc
