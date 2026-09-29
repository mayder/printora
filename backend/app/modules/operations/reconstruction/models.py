from __future__ import annotations

import json

from app.modules.operations.reconstruction.contracts import (
    ReconstructionArtifact,
    ReconstructionAttempt,
    ReconstructionJob,
    MeshQualification,
)


def reconstruction_job_model(row, attempts, artifacts, qualification=None) -> ReconstructionJob:
    status = str(row["status"])
    next_action = {
        "queued": "Você pode sair desta tela. O processamento começará quando houver capacidade.",
        "processing": "Aguarde. Suas fotos estão sendo processadas fora da impressora.",
        "succeeded": "A malha bruta está pronta para a revisão técnica.",
        "failed": "Tente novamente ou escolha outro modo de processamento.",
        "cancelled": "Você pode iniciar novamente quando quiser.",
    }[status]
    return ReconstructionJob(
        id=int(row["id"]), capture_session_id=int(row["capture_session_id"]), project_id=int(row["project_id"]),
        status=status, stage=str(row["stage"]), progress_percent=row["progress_percent"],
        engine_policy=str(row["engine_policy"]), engine_key=row["engine_key"], correlation_id=str(row["correlation_id"]),
        error_code=row["error_code"], error_message=row["error_message"], estimated_cost_cents=row["estimated_cost_cents"],
        actual_cost_cents=row["actual_cost_cents"], can_cancel=status in {"queued", "processing"},
        can_retry=status in {"failed", "cancelled"}, next_action=next_action,
        created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        attempts=[
            ReconstructionAttempt(
                id=int(item["id"]), attempt_number=int(item["attempt_number"]), engine_key=str(item["engine_key"]),
                adapter_version=str(item["adapter_version"]), status=str(item["status"]), stage=str(item["stage"]),
                estimated_cost_cents=item["estimated_cost_cents"], actual_cost_cents=item["actual_cost_cents"],
                started_at=str(item["started_at"]), completed_at=item["completed_at"],
            )
            for item in attempts
        ],
        artifacts=[
            ReconstructionArtifact(
                id=int(item["id"]), artifact_type=str(item["artifact_type"]), file_format=str(item["file_format"]),
                sha256=str(item["sha256"]), size_bytes=int(item["size_bytes"]), unit=str(item["unit"]),
                observed_ratio=item["observed_ratio"], inferred_ratio=item["inferred_ratio"],
                provenance=json.loads(item["provenance_json"] or "{}"),
            )
            for item in artifacts
        ],
        qualification=(
            MeshQualification(
                id=int(qualification["id"]),
                reconstruction_artifact_id=int(qualification["reconstruction_artifact_id"]),
                analyzer_version=str(qualification["analyzer_version"]),
                status=str(qualification["status"]),
                report=json.loads(qualification["report_json"]),
                created_at=str(qualification["created_at"]),
            )
            if qualification is not None else None
        ),
    )
