from __future__ import annotations

from app.config import Settings
from app.modules.operations.mesh_qualification.repair import repair_mesh
from app.modules.operations.mesh_qualification.repository import MeshRevisionRepository
from app.modules.platform.durable_execution import DurableJob


def execute_mesh_repair(job: DurableJob, settings: Settings) -> dict[str, object]:
    revision_id = int(job.payload["mesh_revision_id"])
    repository = MeshRevisionRepository(settings.database_path, settings)
    source = repository.begin(revision_id, job.id)
    try:
        result = repair_mesh(
            repository.read_source(source), source.source_format,
            source.operation, source.parameters, unit=source.source_unit,
        )
        completed = repository.succeed(source, job.id, result)
        return {"mesh_revision_id": completed.id, "status": completed.status, "sha256": completed.sha256}
    except Exception as exc:
        retryable = job.attempts < job.max_attempts
        repository.fail(
            revision_id, job.id,
            "Não foi possível preparar esta correção. Tente uma opção mais conservadora.",
            retryable,
        )
        if retryable:
            raise RuntimeError("mesh repair failed") from exc
        return {"mesh_revision_id": revision_id, "status": "failed"}
