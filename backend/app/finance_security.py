from __future__ import annotations

import json
from pathlib import Path
import uuid

from app.database import connect_database
from app.modules.finance.contracts import FinanceRoleResponse, RiskCaseResponse


FINANCE_ROLES = {
    "finance_operator", "finance_approver", "finance_risk", "finance_support", "finance_auditor",
}


class FinanceSecurityService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def has_role(self, user_id: int, roles: set[str]) -> bool:
        if not roles <= FINANCE_ROLES:
            raise ValueError("papel financeiro inválido")
        with connect_database(self.database_path) as connection:
            placeholders = ", ".join("?" for _ in roles)
            row = connection.execute(
                f"""
                SELECT 1 FROM finance_role_assignments
                WHERE user_id = ? AND role IN ({placeholders}) AND is_active = ? LIMIT 1
                """,
                (user_id, *sorted(roles), True),
            ).fetchone()
        return row is not None

    def assign_role(
        self, user_id: int, role: str, active: bool, granted_by_user_id: int
    ) -> FinanceRoleResponse:
        if role not in FINANCE_ROLES:
            raise ValueError("papel financeiro inválido")
        with connect_database(self.database_path) as connection:
            if connection.execute("SELECT 1 FROM auth_users WHERE id = ?", (user_id,)).fetchone() is None:
                raise ValueError("usuário não encontrado")
            connection.execute(
                """
                INSERT INTO finance_role_assignments (user_id, role, granted_by_user_id, is_active)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, role) DO UPDATE SET
                    is_active = excluded.is_active,
                    granted_by_user_id = excluded.granted_by_user_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, role, granted_by_user_id, active),
            )
            _audit(
                connection, "finance.role.changed", granted_by_user_id, "user",
                str(user_id), f"finance-role:{user_id}:{role}", {"role": role, "active": active},
            )
        return FinanceRoleResponse(user_id=user_id, role=role, active=active)


class FinanceRiskService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def evaluate_order_in_connection(self, connection, order_id: int) -> RiskCaseResponse:
        existing = connection.execute(
            "SELECT * FROM finance_risk_cases WHERE order_id = ?", (order_id,)
        ).fetchone()
        if existing is not None:
            return _risk_response(existing)
        order = connection.execute("SELECT * FROM commerce_orders WHERE id = ?", (order_id,)).fetchone()
        reasons, score = _risk_rules(connection, order)
        level = "high" if score >= 5000 else "medium" if score >= 2500 else "low"
        action = "review" if score >= 5000 else "allow"
        status = "review_required" if action == "review" else "approved"
        public_id = f"rsk_{uuid.uuid4().hex}"
        connection.execute(
            """
            INSERT INTO finance_risk_cases (
                public_id, order_id, buyer_user_id, score_basis_points, risk_level,
                reason_codes_json, recommended_action, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (public_id, order_id, order["buyer_user_id"], score, level, json.dumps(reasons), action, status),
        )
        row = connection.execute("SELECT * FROM finance_risk_cases WHERE public_id = ?", (public_id,)).fetchone()
        return _risk_response(row)

    def list_cases(self, status: str | None = None) -> list[RiskCaseResponse]:
        with connect_database(self.database_path) as connection:
            query, params = "SELECT * FROM finance_risk_cases", ()
            if status:
                query, params = query + " WHERE status = ?", (status,)
            rows = connection.execute(query + " ORDER BY id DESC LIMIT 200", params).fetchall()
        return [_risk_response(row) for row in rows]

    def decide(self, public_id: str, decision: str, reason: str, actor_user_id: int) -> RiskCaseResponse:
        if decision not in {"approve", "reject"}:
            raise ValueError("decisão de risco inválida")
        with connect_database(self.database_path) as connection:
            row = _risk_case(connection, public_id)
            if row["status"] not in {"review_required", "appealed"}:
                raise ValueError("caso de risco não aguarda decisão")
            connection.execute(
                """
                INSERT INTO finance_risk_decisions (risk_case_id, decision, reason, decided_by_user_id)
                VALUES (?, ?, ?, ?)
                """,
                (row["id"], decision, reason.strip(), actor_user_id),
            )
            connection.execute(
                "UPDATE finance_risk_cases SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("approved" if decision == "approve" else "rejected", row["id"]),
            )
            _audit(
                connection, "finance.risk.decided", actor_user_id, "risk_case", public_id,
                f"risk:{public_id}", {"decision": decision, "reason_code": "human_review"},
            )
            return _risk_response(_risk_case(connection, public_id))

    def appeal(self, public_id: str, reason: str, buyer_user_id: int) -> RiskCaseResponse:
        with connect_database(self.database_path) as connection:
            row = _risk_case(connection, public_id)
            if int(row["buyer_user_id"]) != buyer_user_id or row["status"] != "rejected":
                raise PermissionError("caso não aceita recurso deste usuário")
            connection.execute(
                """
                INSERT INTO finance_risk_decisions (risk_case_id, decision, reason, decided_by_user_id)
                VALUES (?, 'appeal', ?, ?)
                """,
                (row["id"], reason.strip(), buyer_user_id),
            )
            connection.execute(
                "UPDATE finance_risk_cases SET status = 'appealed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],),
            )
            _audit(
                connection, "finance.risk.appealed", buyer_user_id, "risk_case", public_id,
                f"risk:{public_id}", {"reason_code": "buyer_appeal"},
            )
            return _risk_response(_risk_case(connection, public_id))


def _risk_rules(connection, order) -> tuple[list[str], int]:
    reasons: list[str] = []
    score = 0
    if int(order["total_minor"]) >= 100_000:
        reasons.append("high_amount")
        score += 5000
    recent = connection.execute(
        "SELECT COUNT(*) AS total FROM commerce_orders WHERE buyer_user_id = ?",
        (order["buyer_user_id"],),
    ).fetchone()
    if int(recent["total"]) > 5:
        reasons.append("order_velocity")
        score += 2500
    disputes = connection.execute(
        """
        SELECT COUNT(*) AS total FROM payment_disputes dispute
        JOIN commerce_orders prior ON prior.id = dispute.order_id
        WHERE prior.buyer_user_id = ?
        """,
        (order["buyer_user_id"],),
    ).fetchone()
    if int(disputes["total"]) > 0:
        reasons.append("prior_dispute")
        score += 3000
    return reasons or ["no_elevated_signal"], min(score, 10000)


def _risk_case(connection, public_id: str):
    row = connection.execute("SELECT * FROM finance_risk_cases WHERE public_id = ?", (public_id,)).fetchone()
    if row is None:
        raise ValueError("caso de risco não encontrado")
    return row


def _risk_response(row) -> RiskCaseResponse:
    return RiskCaseResponse(
        public_id=str(row["public_id"]), order_id=int(row["order_id"]),
        buyer_user_id=int(row["buyer_user_id"]), score_basis_points=int(row["score_basis_points"]),
        risk_level=str(row["risk_level"]), reason_codes=json.loads(row["reason_codes_json"]),
        recommended_action=str(row["recommended_action"]), status=str(row["status"]),
    )


def _audit(connection, event_type, actor, subject_type, subject_id, correlation_id, details) -> None:
    connection.execute(
        """
        INSERT INTO finance_audit_events (
            event_type, actor_user_id, subject_type, subject_public_id,
            correlation_id, details_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_type, actor, subject_type, subject_id, correlation_id, json.dumps(details, sort_keys=True)),
    )
