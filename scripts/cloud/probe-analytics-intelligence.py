#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from app.config import get_settings
from app.database import connect_database
from app.modules.administration.intelligence import IntelligenceRepository
from app.modules.administration.intelligence_contracts import SanitizedEventCreate


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe não destrutivo do pipeline analítico isolado")
    parser.add_argument("--run-key", required=True)
    parser.add_argument("--events", type=int, default=500)
    args = parser.parse_args()
    safe_key = "".join(character for character in args.run_key if character.isalnum() or character in "_-")[:60]
    if len(safe_key) < 8:
        raise SystemExit("run-key inválida")
    event_count = max(10, min(args.events, 5000))
    repository = IntelligenceRepository(get_settings().database_path)
    repository.ensure_schema()
    role = _role_evidence(repository)
    started = time.monotonic()
    for index in range(event_count):
        repository.ingest(_event(
            f"probe:{safe_key}:impact:{index}",
            "impact.observed",
            "product_impact",
            {"metric": "probe_latency_budget", "dimension": "cloud", "value": index % 10},
            f"synthetic-subject-{index % 50}",
        ))
    for language, text in (
        ("pt", "Você é idiota e publicou um telefone."),
        ("en", "This is a stupid scam with a phone."),
        ("es", "Esto es una estafa con odio y telefono."),
    ):
        repository.ingest(_event(
            f"probe:{safe_key}:moderation:{language}",
            "moderation.content_submitted",
            "safety_moderation",
            {"entity_type": "synthetic_probe", "entity_id": language, "text": text},
        ))
    repository.ingest(_event(
        f"probe:{safe_key}:geometry:1",
        "geometry.indexed",
        "geometry_search",
        {"item_key": f"probe-part-{safe_key}", "entity_type": "probe", "features": {"width": 10, "height": 5}},
    ))
    processed_total = 0
    while True:
        result = repository.process_pending(500)
        processed_total += result["processed"]
        if result["processed"] == 0:
            break
    replay_key = f"probe-replay-{safe_key}"
    replay = repository.replay(replay_key)
    replay_again = repository.replay(replay_key)
    anonymization = repository.anonymize_subject("synthetic-subject-1", "product_impact")
    before = _model_state(repository, "recommendation-baseline", "1.0.0")
    try:
        repository.control_model(
            "recommendation-baseline", "1.0.0",
            enabled=True, kill_switch=True, canary_percent=100, drift_score=0,
        )
        fallback = repository.recommend(
            f"probe-decision-{safe_key}", ["project-z", "project-a", "project-m"],
            "synthetic-probe",
        )
    finally:
        repository.control_model(
            "recommendation-baseline", "1.0.0",
            enabled=bool(before["enabled"]),
            kill_switch=bool(before["kill_switch"]),
            canary_percent=int(before["canary_percent"]),
            drift_score=float(before["drift_score"]),
        )
    dashboard = repository.dashboard()
    moderation = [
        item for item in repository.moderation_queue()
        if item["source_event_id"].startswith(f"probe:{safe_key}:moderation:")
    ]
    retention = repository.retention_preview()
    elapsed = time.monotonic() - started
    evidence = {
        "status": "passed",
        "run_key": safe_key,
        "events_requested": event_count + 4,
        "processed_in_probe": processed_total,
        "elapsed_seconds": round(elapsed, 3),
        "events_per_second": round((event_count + 4) / max(elapsed, 0.001), 3),
        "role": role,
        "replay": {
            "processed_count": replay["processed_count"],
            "unchanged_count": replay["unchanged_count"],
            "second_call_idempotent": replay_again["idempotent"],
        },
        "anonymization": anonymization,
        "moderation_languages": sorted(item["detected_language"] for item in moderation),
        "moderation_human_review": all(bool(item["human_review_required"]) for item in moderation),
        "fallback": fallback,
        "temporary_records": dashboard["temporary_records"],
        "retention_mode": retention["mode"],
        "retention_deleted_data": retention["data_deleted"],
        "models": [
            {
                "model_key": model["model_key"],
                "version": model["version"],
                "owner": model["owner"],
                "dataset_license": model["dataset_license"],
                "fallback_strategy": model["fallback_strategy"],
            }
            for model in dashboard["models"]
        ],
    }
    if role["analytics_can_read_oltp"] or not role["analytics_can_update_derivatives"]:
        raise SystemExit("isolamento da role falhou")
    if not replay_again["idempotent"] or replay["processed_count"] != replay["unchanged_count"]:
        raise SystemExit("replay não idempotente")
    if fallback["items"] != ["project-a", "project-m", "project-z"] or not fallback["fallback_used"]:
        raise SystemExit("fallback não determinístico")
    if sorted(evidence["moderation_languages"]) != ["en", "es", "pt"] or not evidence["moderation_human_review"]:
        raise SystemExit("moderação multilíngue/humana falhou")
    if retention["data_deleted"]:
        raise SystemExit("probe de retenção alterou dados")
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))


def _event(event_id, event_type, purpose, payload, subject_key=None):
    return SanitizedEventCreate(
        event_id=event_id,
        event_type=event_type,
        purpose=purpose,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        subject_key=subject_key,
        payload=payload,
    )


def _role_evidence(repository):
    with connect_database(repository.database_path) as connection:
        connection.execute("SET LOCAL ROLE printora_analytics")
        row = connection.execute(
            """
            SELECT current_user AS role_name,
                   has_table_privilege('analytics_events','UPDATE') AS analytics_update,
                   has_table_privilege('auth_users','SELECT') AS oltp_read,
                   has_table_privilege('auth_users','UPDATE') AS oltp_update
            """
        ).fetchone()
    return {
        "role_name": row["role_name"],
        "analytics_can_update_derivatives": bool(row["analytics_update"]),
        "analytics_can_read_oltp": bool(row["oltp_read"]),
        "analytics_can_write_oltp": bool(row["oltp_update"]),
    }


def _model_state(repository, model_key, version):
    with connect_database(repository.database_path) as connection:
        connection.execute("SET LOCAL ROLE printora_analytics")
        return dict(connection.execute(
            """
            SELECT enabled,kill_switch,canary_percent,drift_score
            FROM analytics_model_registry WHERE model_key=? AND version=?
            """,
            (model_key, version),
        ).fetchone())


if __name__ == "__main__":
    main()
