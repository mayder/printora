from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.database import connect_database, initialize_database
from app.modules.administration.intelligence_contracts import SanitizedEventCreate
from app.modules.administration.intelligence_moderation import assess_text
from app.modules.platform.database_target import uses_postgresql


TRANSFORMATION_VERSION = "analytics-v1"
SENSITIVE_KEYS = {
    "password", "token", "secret", "email", "phone", "telephone", "address",
    "cpf", "cnpj", "ip", "access_token", "refresh_token", "authorization",
}
SAFE_EVENT_PURPOSES = {
    "impact.observed": "product_impact",
    "moderation.content_submitted": "safety_moderation",
    "moderation.report.created": "safety_moderation",
    "recommendation.signal": "recommendation",
    "geometry.indexed": "geometry_search",
    "subject.removal_requested": None,
}


class IntelligenceRepository:
    def __init__(self, database_path) -> None:
        self.database_path = database_path

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def ingest(self, event: SanitizedEventCreate) -> dict[str, Any]:
        self.ensure_schema()
        expected_purpose = SAFE_EVENT_PURPOSES[event.event_type]
        if expected_purpose is not None and event.purpose != expected_purpose:
            raise ValueError("finalidade incompatível com o tipo do evento")
        sanitized = sanitize_payload(event.payload)
        canonical_payload = _canonical(sanitized)
        payload_sha = _sha(canonical_payload)
        subject_hash = hash_subject(event.subject_key) if event.subject_key else None
        retention_until = _iso(_now() + timedelta(days=_retention_days(event.purpose)))
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT payload_sha256, status FROM analytics_events WHERE event_id = ?",
                (event.event_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_sha:
                    raise ValueError("event_id repetido com conteúdo divergente")
                return {"event_id": event.event_id, "status": existing["status"], "idempotent": True}
            connection.execute(
                """
                INSERT INTO analytics_events(
                    event_id,event_type,schema_version,purpose,subject_key_hash,occurred_at,
                    payload_json,payload_sha256,retention_until
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.event_id, event.event_type, event.schema_version, event.purpose,
                    subject_hash, event.occurred_at, canonical_payload, payload_sha, retention_until,
                ),
            )
            if subject_hash:
                connection.execute(
                    """
                    INSERT INTO analytics_subject_controls(subject_key_hash,purpose,consent_state)
                    VALUES(?,?,'not_required')
                    ON CONFLICT(subject_key_hash) DO UPDATE SET purpose=excluded.purpose,updated_at=CURRENT_TIMESTAMP
                    """,
                    (subject_hash, event.purpose),
                )
        return {"event_id": event.event_id, "status": "pending", "idempotent": False}

    def process_pending(self, limit: int = 100) -> dict[str, int]:
        self.ensure_schema()
        processed = 0
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            rows = connection.execute(
                """
                SELECT * FROM analytics_events
                WHERE status = 'pending'
                ORDER BY created_at,event_id LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
            for row in rows:
                self._process_event(connection, row)
                processed += 1
        return {"processed": processed}

    def replay(self, replay_key: str, event_type: str | None = None) -> dict[str, Any]:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            previous = connection.execute(
                "SELECT * FROM analytics_replay_runs WHERE replay_key = ?",
                (replay_key,),
            ).fetchone()
            if previous is not None:
                return dict(previous) | {"idempotent": True}
            source_filter = event_type or "*"
            connection.execute(
                "INSERT INTO analytics_replay_runs(replay_key,source_filter,status) VALUES(?,?,'running')",
                (replay_key, source_filter),
            )
            if event_type:
                rows = connection.execute(
                    "SELECT * FROM analytics_events WHERE event_type = ? ORDER BY event_id",
                    (event_type,),
                ).fetchall()
            else:
                rows = connection.execute("SELECT * FROM analytics_events ORDER BY event_id").fetchall()
            before = self._derivative_digest(connection)
            for row in rows:
                self._process_event(connection, row, replay=True)
            after = self._derivative_digest(connection)
            unchanged = len(rows) if before == after else 0
            connection.execute(
                """
                UPDATE analytics_replay_runs
                SET status='completed',processed_count=?,unchanged_count=?,output_sha256=?,completed_at=CURRENT_TIMESTAMP
                WHERE replay_key=?
                """,
                (len(rows), unchanged, after, replay_key),
            )
            result = connection.execute(
                "SELECT * FROM analytics_replay_runs WHERE replay_key=?", (replay_key,)
            ).fetchone()
        return dict(result) | {"idempotent": False}

    def dashboard(self) -> dict[str, Any]:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            status = connection.execute(
                "SELECT status,COUNT(*) total FROM analytics_events GROUP BY status ORDER BY status"
            ).fetchall()
            moderation = connection.execute(
                "SELECT status,COUNT(*) total FROM analytics_moderation_cases GROUP BY status ORDER BY status"
            ).fetchall()
            models = connection.execute(
                """
                SELECT model_key,version,owner,dataset_name,dataset_version,dataset_license,
                       metrics_json,bias_assessment_json,canary_percent,drift_score,drift_threshold,
                       enabled,kill_switch,fallback_strategy,rollback_version
                FROM analytics_model_registry ORDER BY model_key,version DESC
                """
            ).fetchall()
            metrics = connection.execute(
                """
                SELECT metric_name,dimension_key,COUNT(*) samples,AVG(value) average_value,MAX(bucket_at) latest_bucket
                FROM analytics_metric_facts GROUP BY metric_name,dimension_key ORDER BY metric_name,dimension_key
                """
            ).fetchall()
            temporary = connection.execute(
                """
                SELECT COUNT(*) total FROM analytics_events e
                JOIN analytics_retention_policies p ON p.purpose=e.purpose
                WHERE p.temporary_data=1
                """
            ).fetchone()
            lineage = connection.execute(
                """
                SELECT source_event_id,derivative_type,derivative_key,transformation_version,
                       output_sha256,created_at
                FROM analytics_lineage ORDER BY created_at DESC LIMIT 100
                """
            ).fetchall()
            replays = connection.execute(
                "SELECT * FROM analytics_replay_runs ORDER BY started_at DESC LIMIT 20"
            ).fetchall()
        return {
            "pipeline": [dict(row) for row in status],
            "impact": [dict(row) for row in metrics],
            "moderation": [dict(row) for row in moderation],
            "models": [_decode_model(row) for row in models],
            "temporary_records": int(temporary["total"]),
            "lineage": [dict(row) for row in lineage],
            "replays": [dict(row) for row in replays],
            "isolation": {
                "source": "sanitized_events_only",
                "oltp_writes": False,
                "transformation_version": TRANSFORMATION_VERSION,
            },
        }

    def moderation_queue(self) -> list[dict[str, Any]]:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            rows = connection.execute(
                "SELECT * FROM analytics_moderation_cases ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        return [_decode_json_fields(dict(row), ("labels_json",)) for row in rows]

    def review_case(self, case_key: str, decision: str, rationale: str, reviewer_key: str) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            updated = connection.execute(
                """
                UPDATE analytics_moderation_cases SET status=?,rationale=?,reviewer_key_hash=?,
                    reviewed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE case_key=?
                """,
                (decision, rationale, hash_subject(reviewer_key), case_key),
            )
            if updated.rowcount != 1:
                raise ValueError("caso de moderação não encontrado")
            row = connection.execute(
                "SELECT * FROM analytics_moderation_cases WHERE case_key=?", (case_key,)
            ).fetchone()
        return _decode_json_fields(dict(row), ("labels_json",))

    def create_appeal(self, appeal_key: str, case_key: str, appellant_key: str, reason: str) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            case = connection.execute(
                "SELECT case_key FROM analytics_moderation_cases WHERE case_key=?", (case_key,)
            ).fetchone()
            if case is None:
                raise ValueError("caso de moderação não encontrado")
            connection.execute(
                """
                INSERT INTO analytics_moderation_appeals(
                    appeal_key,case_key,appellant_key_hash,reason_sha256,status
                ) VALUES(?,?,?,?,'open') ON CONFLICT(appeal_key) DO NOTHING
                """,
                (appeal_key, case_key, hash_subject(appellant_key), _sha(reason)),
            )
            connection.execute(
                "UPDATE analytics_moderation_cases SET status='appealed',updated_at=CURRENT_TIMESTAMP WHERE case_key=?",
                (case_key,),
            )
            row = connection.execute(
                "SELECT * FROM analytics_moderation_appeals WHERE appeal_key=?", (appeal_key,)
            ).fetchone()
        return dict(row)

    def review_appeal(self, appeal_key: str, decision: str, resolution: str, reviewer_key: str) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            updated = connection.execute(
                """
                UPDATE analytics_moderation_appeals SET status=?,resolution=?,reviewer_key_hash=?,
                    resolved_at=CURRENT_TIMESTAMP WHERE appeal_key=? AND status='open'
                """,
                (decision, resolution, hash_subject(reviewer_key), appeal_key),
            )
            if updated.rowcount != 1:
                raise ValueError("recurso aberto não encontrado")
            row = connection.execute(
                "SELECT * FROM analytics_moderation_appeals WHERE appeal_key=?", (appeal_key,)
            ).fetchone()
        return dict(row)

    def anonymize_subject(self, subject_key: str, purpose: str) -> dict[str, Any]:
        subject_hash = hash_subject(subject_key)
        anonymous_hash = _sha(f"anonymized:{subject_hash}")
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            connection.execute(
                """
                INSERT INTO analytics_subject_controls(
                    subject_key_hash,purpose,consent_state,removal_requested_at,deadline_at
                ) VALUES(?,?,'withdrawn',CURRENT_TIMESTAMP,?)
                ON CONFLICT(subject_key_hash) DO UPDATE SET consent_state='withdrawn',
                    removal_requested_at=CURRENT_TIMESTAMP,deadline_at=excluded.deadline_at,updated_at=CURRENT_TIMESTAMP
                """,
                (subject_hash, purpose, _iso(_now() + timedelta(hours=24))),
            )
            counts: dict[str, int] = {}
            for table in ("analytics_events", "analytics_model_decisions"):
                result = connection.execute(
                    f"UPDATE {table} SET subject_key_hash=? WHERE subject_key_hash=?",
                    (anonymous_hash, subject_hash),
                )
                counts[table] = result.rowcount
            connection.execute(
                """
                UPDATE analytics_subject_controls SET anonymized_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                WHERE subject_key_hash=?
                """,
                (subject_hash,),
            )
        return {"subject_key_hash": subject_hash, "anonymized": True, "derivatives_updated": counts}

    def control_model(
        self, model_key: str, version: str, *, enabled: bool, kill_switch: bool,
        canary_percent: int, drift_score: float,
    ) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            updated = connection.execute(
                """
                UPDATE analytics_model_registry SET enabled=?,kill_switch=?,canary_percent=?,
                    drift_score=?,updated_at=CURRENT_TIMESTAMP WHERE model_key=? AND version=?
                """,
                (int(enabled), int(kill_switch), canary_percent, drift_score, model_key, version),
            )
            if updated.rowcount != 1:
                raise ValueError("modelo não encontrado")
            row = connection.execute(
                "SELECT * FROM analytics_model_registry WHERE model_key=? AND version=?",
                (model_key, version),
            ).fetchone()
        return _decode_model(row)

    def recommend(
        self, decision_key: str, candidates: list[str], subject_key: str | None = None
    ) -> dict[str, Any]:
        return self._deterministic_decision(
            decision_key, "recommendation-baseline", candidates, subject_key,
            lambda values: sorted(set(values), key=lambda value: _sha(f"{subject_key or 'anon'}:{value}")),
        )

    def geometry_search(
        self, decision_key: str, entity_type: str, features: dict[str, float], limit: int
    ) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            model = self._active_model(connection, "geometry-baseline")
            rows = connection.execute(
                "SELECT item_key,features_json FROM analytics_geometry_items WHERE entity_type=? AND active=1",
                (entity_type,),
            ).fetchall()
            fallback = _model_fallback(model, decision_key)
            if fallback:
                ranked = [row["item_key"] for row in sorted(rows, key=lambda row: row["item_key"])]
            else:
                ranked = [
                    item_key for _, item_key in sorted(
                        (
                            (_normalized_l1(features, json.loads(row["features_json"])), row["item_key"])
                            for row in rows
                        ),
                        key=lambda item: (item[0], item[1]),
                    )
                ]
            output = ranked[:limit]
            self._record_decision(connection, decision_key, model, features, output, fallback, None)
        return {"items": output, "fallback_used": fallback, "model_version": model["version"]}

    def retention_preview(self) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            policies = connection.execute(
                "SELECT * FROM analytics_retention_policies ORDER BY purpose"
            ).fetchall()
            expired = connection.execute(
                """
                SELECT purpose,COUNT(*) total FROM analytics_events
                WHERE retention_until < CURRENT_TIMESTAMP GROUP BY purpose ORDER BY purpose
                """
            ).fetchall()
        return {
            "mode": "preview_only",
            "policies": [dict(row) for row in policies],
            "expired": [dict(row) for row in expired],
            "data_deleted": False,
        }

    def _deterministic_decision(self, decision_key, model_key, values, subject_key, ranker):
        with connect_database(self.database_path) as connection:
            self._activate_analytics_role(connection)
            existing = connection.execute(
                "SELECT * FROM analytics_model_decisions WHERE decision_key=?", (decision_key,)
            ).fetchone()
            if existing is not None:
                return {
                    "items": json.loads(existing["output_json"]),
                    "fallback_used": bool(existing["fallback_used"]),
                    "model_version": existing["model_version"],
                    "idempotent": True,
                }
            model = self._active_model(connection, model_key)
            fallback = _model_fallback(model, decision_key)
            output = sorted(set(values)) if fallback else ranker(values)
            self._record_decision(connection, decision_key, model, values, output, fallback, subject_key)
        return {"items": output, "fallback_used": fallback, "model_version": model["version"], "idempotent": False}

    def _record_decision(self, connection, key, model, input_value, output, fallback, subject_key):
        connection.execute(
            """
            INSERT INTO analytics_model_decisions(
                decision_key,model_key,model_version,input_sha256,output_json,fallback_used,subject_key_hash
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                key, model["model_key"], model["version"], _sha(_canonical(input_value)),
                _canonical(output), int(fallback), hash_subject(subject_key) if subject_key else None,
            ),
        )

    def _active_model(self, connection, model_key):
        row = connection.execute(
            "SELECT * FROM analytics_model_registry WHERE model_key=? ORDER BY version DESC LIMIT 1",
            (model_key,),
        ).fetchone()
        if row is None:
            raise RuntimeError("registro de modelo ausente")
        return row

    def _process_event(self, connection, row, replay: bool = False) -> None:
        payload = json.loads(row["payload_json"])
        event_type = row["event_type"]
        derivative_type = "event"
        derivative_key = row["event_id"]
        output: object = {"status": "observed"}
        if event_type == "impact.observed":
            derivative_type, derivative_key, output = self._process_metric(connection, row, payload)
        elif event_type in {"moderation.content_submitted", "moderation.report.created"}:
            derivative_type, derivative_key, output = self._process_moderation(connection, row, payload)
        elif event_type == "geometry.indexed":
            derivative_type, derivative_key, output = self._process_geometry(connection, row, payload)
        elif event_type == "recommendation.signal":
            derivative_type, derivative_key, output = self._process_metric(connection, row, payload)
        elif event_type == "subject.removal_requested" and row["subject_key_hash"]:
            output = {"status": "requires_subject_api"}
        lineage_key = _sha(f"{row['event_id']}:{derivative_type}:{derivative_key}")
        output_sha = _sha(_canonical(output))
        connection.execute(
            """
            INSERT INTO analytics_lineage(
                lineage_key,source_event_id,derivative_type,derivative_key,transformation_version,output_sha256
            ) VALUES(?,?,?,?,?,?)
            ON CONFLICT(lineage_key) DO UPDATE SET output_sha256=excluded.output_sha256
            """,
            (lineage_key, row["event_id"], derivative_type, derivative_key, TRANSFORMATION_VERSION, output_sha),
        )
        if not replay:
            connection.execute(
                "UPDATE analytics_events SET status='processed',processed_at=CURRENT_TIMESTAMP WHERE event_id=?",
                (row["event_id"],),
            )

    def _process_metric(self, connection, row, payload):
        metric_name = str(payload.get("metric", "event_count"))[:80]
        dimension = str(payload.get("dimension", row["event_type"]))[:120]
        value = float(payload.get("value", 1))
        if not math.isfinite(value):
            raise ValueError("métrica não finita")
        fact_key = _sha(f"{row['event_id']}:{metric_name}:{dimension}")
        connection.execute(
            """
            INSERT INTO analytics_metric_facts(
                fact_key,source_event_id,metric_name,dimension_key,value,bucket_at
            ) VALUES(?,?,?,?,?,?)
            ON CONFLICT(fact_key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP
            """,
            (fact_key, row["event_id"], metric_name, dimension, value, row["occurred_at"]),
        )
        return "metric_fact", fact_key, {"metric": metric_name, "dimension": dimension, "value": value}

    def _process_moderation(self, connection, row, payload):
        text = str(payload.get("text") or payload.get("detail") or payload.get("reason") or "")
        assessment = assess_text(text)
        case_key = f"moderation:{row['event_id']}"
        labels_json = _canonical(list(assessment.labels))
        entity_type = str(payload.get("entity_type", "unknown"))[:80]
        entity_reference_hash = _sha(str(payload.get("entity_id", "unknown")))
        connection.execute(
            """
            INSERT INTO analytics_moderation_cases(
                case_key,source_event_id,entity_type,entity_reference_hash,detected_language,
                confidence,labels_json,context_sha256,human_review_required,status
            ) VALUES(?,?,?,?,?,?,?,?,?,'awaiting_review')
            ON CONFLICT(case_key) DO UPDATE SET detected_language=excluded.detected_language,
                confidence=excluded.confidence,labels_json=excluded.labels_json,
                human_review_required=excluded.human_review_required,updated_at=CURRENT_TIMESTAMP
            """,
            (
                case_key, row["event_id"], entity_type, entity_reference_hash, assessment.language,
                assessment.confidence, labels_json, _sha(text), int(assessment.human_review_required),
            ),
        )
        # Raw context is transient: only non-reversible evidence remains after classification.
        minimized = _canonical({"entity_type": entity_type, "context_sha256": _sha(text)})
        connection.execute(
            "UPDATE analytics_events SET payload_json=?,payload_sha256=? WHERE event_id=?",
            (minimized, _sha(minimized), row["event_id"]),
        )
        return "moderation_case", case_key, {
            "language": assessment.language,
            "labels": assessment.labels,
            "human_review_required": assessment.human_review_required,
        }

    def _process_geometry(self, connection, row, payload):
        item_key = str(payload["item_key"])[:160]
        features = {
            str(key)[:80]: float(value)
            for key, value in dict(payload.get("features") or {}).items()
            if math.isfinite(float(value))
        }
        if not features:
            raise ValueError("features geométricas ausentes")
        canonical = _canonical(features)
        connection.execute(
            """
            INSERT INTO analytics_geometry_items(
                item_key,entity_type,entity_reference_hash,features_json,features_sha256,source_event_id
            ) VALUES(?,?,?,?,?,?)
            ON CONFLICT(item_key) DO UPDATE SET features_json=excluded.features_json,
                features_sha256=excluded.features_sha256,source_event_id=excluded.source_event_id,
                active=1,updated_at=CURRENT_TIMESTAMP
            """,
            (
                item_key, str(payload.get("entity_type", "model"))[:80], _sha(item_key),
                canonical, _sha(canonical), row["event_id"],
            ),
        )
        return "geometry_item", item_key, features

    def _derivative_digest(self, connection) -> str:
        fragments: list[str] = []
        for table, columns in (
            ("analytics_metric_facts", "fact_key,value"),
            ("analytics_moderation_cases", "case_key,labels_json,confidence,status"),
            ("analytics_geometry_items", "item_key,features_sha256,active"),
            ("analytics_lineage", "lineage_key,output_sha256"),
        ):
            rows = connection.execute(f"SELECT {columns} FROM {table} ORDER BY 1").fetchall()
            fragments.extend(_canonical(dict(row)) for row in rows)
        return _sha("\n".join(fragments))

    @staticmethod
    def _activate_analytics_role(connection) -> None:
        if uses_postgresql():
            connection.execute("SET LOCAL ROLE printora_analytics")


def sanitize_payload(value: dict[str, object]) -> dict[str, object]:
    encoded = _sanitize(value, depth=0)
    canonical = _canonical(encoded)
    if len(canonical.encode("utf-8")) > 32_768:
        raise ValueError("evento sanitizado excede 32 KB")
    return encoded


def _sanitize(value: Any, depth: int) -> Any:
    if depth > 5:
        raise ValueError("evento excede profundidade permitida")
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            clean_key = str(key).strip().lower()
            if clean_key in SENSITIVE_KEYS or any(token in clean_key for token in ("password", "secret", "token")):
                raise ValueError(f"campo sensível proibido: {clean_key}")
            result[str(key)[:80]] = _sanitize(item, depth + 1)
        return result
    if isinstance(value, list):
        return [_sanitize(item, depth + 1) for item in value[:100]]
    if isinstance(value, str):
        cleaned = " ".join(value.strip().split())[:4000]
        if re.search(r"\b(?:bearer\s+)?[A-Za-z0-9_-]{32,}\b", cleaned, re.IGNORECASE):
            raise ValueError("possível credencial no evento")
        return cleaned
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ValueError("tipo de dado não permitido no evento")


def hash_subject(value: str) -> str:
    return _sha(f"printora-analytics-subject-v1:{value}")


def _retention_days(purpose: str) -> int:
    return {"product_impact": 730, "safety_moderation": 365, "recommendation": 90, "geometry_search": 180}[purpose]


def _normalized_l1(expected: dict[str, float], actual: dict[str, float]) -> float:
    keys = set(expected) | set(actual)
    return sum(abs(float(expected.get(key, 0)) - float(actual.get(key, 0))) for key in keys) / max(1, len(keys))


def _model_fallback(model, decision_key: str) -> bool:
    if bool(model["kill_switch"]) or not bool(model["enabled"]):
        return True
    if float(model["drift_score"]) > float(model["drift_threshold"]):
        return True
    canary_bucket = int(_sha(decision_key)[:8], 16) % 100
    return canary_bucket >= int(model["canary_percent"])


def _decode_model(row) -> dict[str, Any]:
    result = dict(row)
    result["metrics"] = json.loads(result.pop("metrics_json"))
    result["bias_assessment"] = json.loads(result.pop("bias_assessment_json"))
    result["enabled"] = bool(result["enabled"])
    result["kill_switch"] = bool(result["kill_switch"])
    return result


def _decode_json_fields(value: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    for field in fields:
        value[field.removesuffix("_json")] = json.loads(value.pop(field))
    return value


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
