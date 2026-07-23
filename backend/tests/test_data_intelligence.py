from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.modules.administration.intelligence import (
    IntelligenceRepository,
    hash_subject,
    sanitize_payload,
)
from app.modules.administration.intelligence_contracts import SanitizedEventCreate


def event(event_id: str, event_type: str, purpose: str, payload: dict, subject_key: str | None = None):
    return SanitizedEventCreate(
        event_id=event_id,
        event_type=event_type,
        purpose=purpose,
        occurred_at="2026-07-23T12:00:00Z",
        subject_key=subject_key,
        payload=payload,
    )


def repository(tmp_path: Path) -> IntelligenceRepository:
    database_path = tmp_path / "analytics.db"
    initialize_database(database_path)
    return IntelligenceRepository(database_path)


def test_sanitized_pipeline_is_idempotent_and_replay_preserves_derivatives(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    payload = {"metric": "print_success", "dimension": "cloud", "value": 1}

    first = repo.ingest(event("impact-event-0001", "impact.observed", "product_impact", payload))
    duplicate = repo.ingest(event("impact-event-0001", "impact.observed", "product_impact", payload))
    processed = repo.process_pending()
    first_replay = repo.replay("replay-impact-0001")
    duplicate_replay = repo.replay("replay-impact-0001")

    assert first == {"event_id": "impact-event-0001", "status": "pending", "idempotent": False}
    assert duplicate["idempotent"] is True
    assert processed == {"processed": 1}
    assert first_replay["processed_count"] == 1
    assert first_replay["unchanged_count"] == 1
    assert duplicate_replay["idempotent"] is True
    with connect_database(repo.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) total FROM analytics_metric_facts").fetchone()["total"] == 1
        assert connection.execute("SELECT COUNT(*) total FROM analytics_lineage").fetchone()["total"] == 1


def test_multilingual_moderation_requires_human_review_and_discards_context(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    repo.ingest(event(
        "moderation-event-0001",
        "moderation.content_submitted",
        "safety_moderation",
        {"entity_type": "post", "entity_id": 42, "text": "Você é idiota, meu telefone está aqui"},
    ))

    repo.process_pending()
    cases = repo.moderation_queue()
    reviewed = repo.review_case(
        cases[0]["case_key"], "rejected", "Revisão humana confirmou o risco.", "reviewer@example.com",
    )
    appeal = repo.create_appeal(
        "appeal-event-0001", cases[0]["case_key"], "maker-42", "Solicito uma nova revisão.",
    )
    resolved = repo.review_appeal(
        appeal["appeal_key"], "upheld", "Decisão revertida após revisão independente.", "reviewer-2@example.com",
    )

    assert cases[0]["detected_language"] == "pt"
    assert cases[0]["human_review_required"] == 1
    assert {"harassment", "privacy"}.issubset(set(cases[0]["labels"]))
    assert reviewed["status"] == "rejected"
    assert resolved["status"] == "upheld"
    with connect_database(repo.database_path) as connection:
        stored = connection.execute(
            "SELECT payload_json FROM analytics_events WHERE event_id='moderation-event-0001'"
        ).fetchone()["payload_json"]
    assert "idiota" not in stored
    assert "telefone" not in stored


def test_anonymization_propagates_to_derived_decisions_with_no_delete(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    repo.ingest(event(
        "recommend-event-0001", "recommendation.signal", "recommendation",
        {"metric": "interaction", "dimension": "project", "value": 1}, "user-42",
    ))
    repo.process_pending()
    repo.recommend("decision-event-0001", ["project-b", "project-a"], "user-42")

    result = repo.anonymize_subject("user-42", "recommendation")

    assert result["anonymized"] is True
    assert result["derivatives_updated"]["analytics_events"] == 1
    assert result["derivatives_updated"]["analytics_model_decisions"] == 1
    with connect_database(repo.database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) total FROM analytics_events WHERE subject_key_hash=?",
            (hash_subject("user-42"),),
        ).fetchone()["total"] == 0
        assert connection.execute("SELECT COUNT(*) total FROM analytics_events").fetchone()["total"] == 1


def test_model_kill_switch_and_drift_use_deterministic_fallback(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    normal = repo.recommend("decision-normal-0001", ["z", "a", "m"], "maker")
    repo.control_model(
        "recommendation-baseline", "1.0.0",
        enabled=True, kill_switch=True, canary_percent=100, drift_score=0,
    )
    fallback = repo.recommend("decision-fallback-0001", ["z", "a", "m"], "maker")

    assert normal["fallback_used"] is False
    assert fallback["fallback_used"] is True
    assert fallback["items"] == ["a", "m", "z"]
    assert repo.recommend("decision-fallback-0001", ["z", "a", "m"], "maker")["idempotent"] is True


def test_geometry_search_isolated_read_model_and_safe_fallback(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    for index, width in enumerate((10.0, 20.0), start=1):
        repo.ingest(event(
            f"geometry-event-000{index}", "geometry.indexed", "geometry_search",
            {"item_key": f"part-{index}", "entity_type": "part", "features": {"width": width, "height": 5}},
        ))
    repo.process_pending()

    result = repo.geometry_search("geometry-decision-0001", "part", {"width": 11, "height": 5}, 2)

    assert result["items"] == ["part-1", "part-2"]
    assert result["fallback_used"] is False


def test_sensitive_fields_and_divergent_event_ids_are_rejected(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    with pytest.raises(ValueError, match="sensível"):
        sanitize_payload({"access_token": "do-not-store"})
    repo.ingest(event(
        "impact-event-0002", "impact.observed", "product_impact",
        {"metric": "quality", "value": 1},
    ))
    with pytest.raises(ValueError, match="divergente"):
        repo.ingest(event(
            "impact-event-0002", "impact.observed", "product_impact",
            {"metric": "quality", "value": 2},
        ))


def test_cloud_intelligence_role_has_no_oltp_grant_and_worker_has_resource_caps() -> None:
    root = Path(__file__).resolve().parents[2]
    permissions = (root / "scripts/cloud/postgresql-runtime-permissions.sql").read_text()
    service = (root / "packaging/systemd/printora-cloud-intelligence.service").read_text()

    assert "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM printora_analytics" in permissions
    assert "GRANT SELECT, INSERT, UPDATE ON TABLE" in permissions
    analytics_grant = permissions.split("GRANT SELECT, INSERT, UPDATE ON TABLE", 1)[1].split(
        "TO printora_analytics", 1
    )[0]
    assert "auth_users" not in analytics_grant
    assert "CPUQuota=50%" in service
    assert "MemoryMax=1G" in service
    assert "TasksMax=128" in service
    assert "NoNewPrivileges=true" in service
