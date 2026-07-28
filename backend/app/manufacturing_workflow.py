from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from app.database import connect_database


TRANSITIONS = {
    "reserved": {"queued", "cancelled"},
    "queued": {"producing", "cancelled"},
    "producing": {"paused", "failed", "quality_pending", "cancelled"},
    "paused": {"producing", "cancelled"},
    "failed": {"rework", "cancelled"},
    "quality_pending": {"rework", "quality_approved"},
    "rework": {"producing", "cancelled"},
    "quality_approved": {"packed"},
    "packed": {"shipped"},
    "shipped": {"delivered"},
    "delivered": {"recalled"},
    "cancelled": set(),
    "recalled": set(),
}


class ManufacturingWorkflowService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create_quote(self, order_public_id: str, payload: dict, actor_user_id: int) -> dict:
        required = ("material", "machine", "files", "tolerance", "finish", "shipping")
        if any(key not in payload for key in required):
            raise ValueError("snapshot de cotação incompleto")
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM manufacturing_quotes WHERE idempotency_key = ?",
                (payload["idempotency_key"],),
            ).fetchone()
            if existing:
                return dict(existing)
            order = connection.execute(
                "SELECT * FROM commerce_orders WHERE public_id = ? AND status = 'paid'",
                (order_public_id,),
            ).fetchone()
            if not order:
                raise ValueError("pedido pago não encontrado")
            items = connection.execute(
                "SELECT license_snapshot, project_snapshot_json FROM commerce_order_items WHERE order_id = ? ORDER BY id",
                (order["id"],),
            ).fetchall()
            if not items or any(not row["license_snapshot"] for row in items):
                raise ValueError("licença de fabricação ausente")
            version = int(connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 AS version FROM manufacturing_quotes WHERE order_id = ?",
                (order["id"],),
            ).fetchone()["version"])
            public_id = f"quote_{uuid4().hex}"
            connection.execute(
                """INSERT INTO manufacturing_quotes (
                    public_id, order_id, version, idempotency_key, material_snapshot_json,
                    machine_snapshot_json, file_snapshot_json, license_snapshot,
                    tolerance_snapshot_json, finish_snapshot_json, shipping_snapshot_json,
                    amount_minor, currency, lead_time_days, status, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'offered', ?)""",
                (public_id, order["id"], version, payload["idempotency_key"],
                 _json(payload["material"]), _json(payload["machine"]), _json(payload["files"]),
                 _json([row["license_snapshot"] for row in items]), _json(payload["tolerance"]),
                 _json(payload["finish"]), _json(payload["shipping"]), int(payload["amount_minor"]),
                 str(payload["currency"]).upper(), int(payload["lead_time_days"]), actor_user_id),
            )
            return dict(connection.execute(
                "SELECT * FROM manufacturing_quotes WHERE public_id = ?", (public_id,)
            ).fetchone())

    def accept_and_reserve(
        self, quote_public_id: str, buyer_user_id: int, resources: list[dict], idempotency_key: str
    ) -> dict:
        with connect_database(self.database_path) as connection:
            quote = connection.execute(
                """SELECT q.*, o.buyer_user_id FROM manufacturing_quotes q
                   JOIN commerce_orders o ON o.id = q.order_id WHERE q.public_id = ?""",
                (quote_public_id,),
            ).fetchone()
            if not quote or int(quote["buyer_user_id"]) != buyer_user_id:
                raise ValueError("cotação não encontrada")
            existing = connection.execute(
                """SELECT mo.* FROM manufacturing_orders mo
                   JOIN manufacturing_quotes q ON q.id = mo.quote_id WHERE q.public_id = ?""",
                (quote_public_id,),
            ).fetchone()
            if existing:
                return dict(existing)
            if quote["status"] != "offered":
                raise ValueError("cotação não pode ser aceita")
            public_id = f"mfg_{uuid4().hex}"
            connection.execute(
                "UPDATE manufacturing_quotes SET status = 'accepted', accepted_by_user_id = ?, accepted_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'offered'",
                (buyer_user_id, quote["id"]),
            )
            manufacturing_id = connection.execute(
                "INSERT INTO manufacturing_orders (public_id, quote_id, order_id, state) VALUES (?, ?, ?, 'reserved')",
                (public_id, quote["id"], quote["order_id"]),
            ).lastrowid
            for index, reservation in enumerate(resources):
                updated = connection.execute(
                    """UPDATE manufacturing_resources SET available_units = available_units - ?, updated_at = CURRENT_TIMESTAMP
                       WHERE resource_key = ? AND available_units >= ?""",
                    (reservation["units"], reservation["resource_key"], reservation["units"]),
                )
                if updated.rowcount != 1:
                    raise ValueError("capacidade ou material indisponível")
                resource = connection.execute(
                    "SELECT id FROM manufacturing_resources WHERE resource_key = ?", (reservation["resource_key"],)
                ).fetchone()
                connection.execute(
                    "INSERT INTO manufacturing_reservations (manufacturing_order_id, resource_id, units, idempotency_key) VALUES (?, ?, ?, ?)",
                    (manufacturing_id, resource["id"], reservation["units"], f"{idempotency_key}:{index}"),
                )
            self._event(connection, manufacturing_id, idempotency_key, "accepted_and_reserved", None, "reserved", "", buyer_user_id)
            return dict(connection.execute(
                "SELECT * FROM manufacturing_orders WHERE public_id = ?", (public_id,)
            ).fetchone())

    def transition(self, public_id: str, target: str, event_key: str, actor_user_id: int, reason: str = "") -> dict:
        with connect_database(self.database_path) as connection:
            duplicate = connection.execute(
                "SELECT mo.* FROM manufacturing_events e JOIN manufacturing_orders mo ON mo.id=e.manufacturing_order_id WHERE e.event_key=?",
                (event_key,),
            ).fetchone()
            if duplicate:
                return dict(duplicate)
            order = connection.execute("SELECT * FROM manufacturing_orders WHERE public_id = ?", (public_id,)).fetchone()
            if not order or target not in TRANSITIONS.get(str(order["state"]), set()):
                raise ValueError("transição produtiva inválida")
            if target == "quality_approved":
                checks = connection.execute(
                    "SELECT result, inspected_by_user_id, approved_by_user_id FROM manufacturing_quality_checks WHERE manufacturing_order_id = ?",
                    (order["id"],),
                ).fetchall()
                if not checks or any(row["result"] != "passed" or not row["approved_by_user_id"] or row["inspected_by_user_id"] == row["approved_by_user_id"] for row in checks):
                    raise ValueError("qualidade segregada pendente")
            connection.execute(
                "UPDATE manufacturing_orders SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (target, order["id"]),
            )
            self._event(connection, order["id"], event_key, "state_changed", order["state"], target, reason, actor_user_id)
            return dict(connection.execute("SELECT * FROM manufacturing_orders WHERE id = ?", (order["id"],)).fetchone())

    def record_quality(self, public_id: str, check_key: str, specification: dict, measurement: dict,
                       passed: bool, evidence_object_key: str, inspector_id: int, approver_id: int | None) -> dict:
        if approver_id is not None and inspector_id == approver_id:
            raise PermissionError("inspetor não pode aprovar a própria medição")
        with connect_database(self.database_path) as connection:
            order = connection.execute("SELECT id, state FROM manufacturing_orders WHERE public_id=?", (public_id,)).fetchone()
            if not order or order["state"] != "quality_pending":
                raise ValueError("ordem fora da etapa de qualidade")
            connection.execute(
                """INSERT INTO manufacturing_quality_checks (
                    manufacturing_order_id, check_key, specification_json, measurement_json, result,
                    evidence_object_key, inspected_by_user_id, approved_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(manufacturing_order_id, check_key) DO NOTHING""",
                (order["id"], check_key, _json(specification), _json(measurement),
                 "passed" if passed else "failed", evidence_object_key, inspector_id, approver_id),
            )
            return dict(connection.execute(
                "SELECT * FROM manufacturing_quality_checks WHERE manufacturing_order_id=? AND check_key=?",
                (order["id"], check_key),
            ).fetchone())

    def approve_quality(self, public_id: str, check_key: str, approver_id: int) -> dict:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT qc.*, mo.state
                FROM manufacturing_quality_checks qc
                JOIN manufacturing_orders mo ON mo.id = qc.manufacturing_order_id
                WHERE mo.public_id = ? AND qc.check_key = ?
                """,
                (public_id, check_key),
            ).fetchone()
            if row is None or row["state"] != "quality_pending":
                raise ValueError("medição de qualidade não encontrada ou fora da etapa")
            if row["result"] != "passed":
                raise ValueError("somente medição aprovada pode receber aceite")
            if int(row["inspected_by_user_id"]) == approver_id:
                raise PermissionError("inspetor não pode aprovar a própria medição")
            connection.execute(
                """
                UPDATE manufacturing_quality_checks
                SET approved_by_user_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND approved_by_user_id IS NULL
                """,
                (approver_id, row["id"]),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM manufacturing_quality_checks WHERE id = ?",
                    (row["id"],),
                ).fetchone()
            )

    def create_shipment(self, public_id: str, carrier: str, tracking_token: str,
                        address_ciphertext: str, actor_user_id: int) -> dict:
        with connect_database(self.database_path) as connection:
            order = connection.execute("SELECT * FROM manufacturing_orders WHERE public_id=?", (public_id,)).fetchone()
            if not order or order["state"] != "quality_approved":
                raise ValueError("somente peça aprovada pode ser embalada")
            shipment_id = f"ship_{uuid4().hex}"
            connection.execute(
                "INSERT INTO manufacturing_shipments (public_id, manufacturing_order_id, carrier, tracking_token_hash, address_ciphertext, status) VALUES (?, ?, ?, ?, ?, 'packed')",
                (shipment_id, order["id"], carrier, _sha(tracking_token), address_ciphertext),
            )
            self._event(connection, order["id"], f"pack:{shipment_id}", "packed", order["state"], "packed", "", actor_user_id)
            connection.execute("UPDATE manufacturing_orders SET state='packed', updated_at=CURRENT_TIMESTAMP WHERE id=?", (order["id"],))
            return dict(connection.execute("SELECT * FROM manufacturing_shipments WHERE public_id=?", (shipment_id,)).fetchone())

    def track(self, shipment_public_id: str, provider_event_id: str, status: str,
              raw_payload: bytes, occurred_at: str, actor_user_id: int) -> dict:
        states = {"in_transit": "shipped", "delivered": "delivered"}
        with connect_database(self.database_path) as connection:
            shipment = connection.execute("SELECT * FROM manufacturing_shipments WHERE public_id=?", (shipment_public_id,)).fetchone()
            if not shipment:
                raise ValueError("expedição não encontrada")
            existing = connection.execute(
                "SELECT * FROM manufacturing_tracking_events WHERE shipment_id=? AND provider_event_id=?",
                (shipment["id"], provider_event_id),
            ).fetchone()
            if existing:
                return dict(existing)
            connection.execute(
                "INSERT INTO manufacturing_tracking_events (shipment_id, provider_event_id, status, payload_sha256, occurred_at) VALUES (?, ?, ?, ?, ?)",
                (shipment["id"], provider_event_id, status, _sha_bytes(raw_payload), occurred_at),
            )
            connection.execute("UPDATE manufacturing_shipments SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, shipment["id"]))
            target = states.get(status)
            if target:
                current = connection.execute("SELECT state FROM manufacturing_orders WHERE id=?", (shipment["manufacturing_order_id"],)).fetchone()["state"]
                if target in TRANSITIONS.get(str(current), set()):
                    connection.execute("UPDATE manufacturing_orders SET state=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (target, shipment["manufacturing_order_id"]))
                    self._event(connection, shipment["manufacturing_order_id"], f"tracking:{provider_event_id}", "tracking", current, target, "", actor_user_id)
            return dict(connection.execute(
                "SELECT * FROM manufacturing_tracking_events WHERE shipment_id=? AND provider_event_id=?",
                (shipment["id"], provider_event_id),
            ).fetchone())

    def recall(self, public_id: str, evidence_reference: str, actor_user_id: int) -> dict:
        with connect_database(self.database_path) as connection:
            order = connection.execute("SELECT * FROM manufacturing_orders WHERE public_id=?", (public_id,)).fetchone()
            if not order:
                raise ValueError("ordem não encontrada")
            incident_id = f"incident_{uuid4().hex}"
            finance_key = f"manufacturing-recall:{incident_id}"
            row_id = connection.execute(
                """INSERT INTO manufacturing_incidents (
                    public_id, manufacturing_order_id, incident_type, severity, status,
                    evidence_reference_hash, finance_command_key, created_by_user_id
                ) VALUES (?, ?, 'unsafe_product', 'critical', 'recalled', ?, ?, ?)""",
                (incident_id, order["id"], _sha(evidence_reference), finance_key, actor_user_id),
            ).lastrowid
            connection.execute(
                "INSERT INTO manufacturing_recall_items (incident_id, manufacturing_order_id, notification_key, status) VALUES (?, ?, ?, 'identified')",
                (row_id, order["id"], f"notify:{incident_id}:{order['id']}"),
            )
            current = order["state"]
            connection.execute("UPDATE manufacturing_orders SET state='recalled', updated_at=CURRENT_TIMESTAMP WHERE id=?", (order["id"],))
            self._event(connection, order["id"], f"recall:{incident_id}", "recall", current, "recalled", "produto inseguro", actor_user_id)
            return {"public_id": incident_id, "finance_command_key": finance_key, "status": "recalled"}

    @staticmethod
    def _event(connection, order_id, key, event_type, from_state, to_state, reason, actor_id) -> None:
        connection.execute(
            "INSERT INTO manufacturing_events (manufacturing_order_id,event_key,event_type,from_state,to_state,reason,actor_user_id) VALUES (?,?,?,?,?,?,?)",
            (order_id, key, event_type, from_state, to_state, reason, actor_id),
        )


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
