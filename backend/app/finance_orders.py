from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid

from app.database import connect_database
from app.finance_payments import FinancePaymentService
from app.finance_security import FinanceRiskService
from app.modules.finance.contracts import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    PaymentIntentResponse,
)
from app.modules.finance.domain import Money


class FinanceOrderService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(self, buyer_user_id: int, payload: OrderCreateRequest) -> OrderResponse:
        digest = _order_digest(buyer_user_id, payload)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT public_id, command_digest FROM commerce_orders WHERE idempotency_key = ?",
                (payload.idempotency_key,),
            ).fetchone()
            if existing is not None:
                if existing["command_digest"] != digest:
                    raise ValueError("chave idempotente já usada com pedido diferente")
                return self._load(connection, str(existing["public_id"]), buyer_user_id)
            snapshots = [self._project_snapshot(connection, item.project_id, item.quantity) for item in payload.items]
            currencies = {snapshot["currency"] for snapshot in snapshots}
            if len(currencies) != 1:
                raise ValueError("pedido não pode misturar moedas")
            subtotal = sum(int(row["unit_price_minor"]) * int(row["quantity"]) for row in snapshots)
            public_id = f"ord_{uuid.uuid4().hex}"
            order_id = self._insert_order(
                connection, public_id, buyer_user_id, payload, digest, currencies.pop(), subtotal
            )
            for snapshot in snapshots:
                self._insert_item(connection, order_id, snapshot)
            FinanceRiskService(self.database_path).evaluate_order_in_connection(connection, order_id)
            return self._load(connection, public_id, buyer_user_id)

    def detail(self, public_id: str, buyer_user_id: int) -> OrderResponse:
        with connect_database(self.database_path) as connection:
            return self._load(connection, public_id, buyer_user_id)

    def checkout(
        self,
        public_id: str,
        buyer_user_id: int,
        idempotency_key: str,
        payment_service: FinancePaymentService,
    ) -> PaymentIntentResponse:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM commerce_orders WHERE public_id = ? AND buyer_user_id = ?",
                (public_id, buyer_user_id),
            ).fetchone()
            if row is None:
                raise ValueError("pedido não encontrado")
            if row["status"] not in {"draft", "pending_payment"}:
                raise ValueError("pedido não aceita novo checkout")
            order_id = int(row["id"])
            money = Money(int(row["total_minor"]), str(row["currency"]))
        intent = payment_service.create_intent(idempotency_key, money, buyer_user_id, order_id)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE commerce_orders SET status = 'pending_payment', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status IN ('draft', 'pending_payment')
                """,
                (order_id,),
            )
            connection.execute(
                """
                UPDATE finance_risk_cases SET payment_intent_id = (
                    SELECT id FROM payment_intents WHERE public_id = ?
                ), updated_at = CURRENT_TIMESTAMP WHERE order_id = ?
                """,
                (intent.public_id, order_id),
            )
        return intent

    @staticmethod
    def _project_snapshot(connection, project_id: int, quantity: int) -> dict[str, object]:
        row = connection.execute(
            """
            SELECT id, owner_user_id, title, license, current_version_id, price_cents,
                   currency, commercial_terms, publication_status, commercial_class,
                   visibility, lifecycle_status
            FROM print_projects WHERE id = ?
            """,
            (project_id,),
        ).fetchone()
        if row is None:
            raise ValueError("projeto não encontrado")
        if (
            row["lifecycle_status"] != "active" or row["visibility"] != "public"
            or row["publication_status"] != "approved" or row["commercial_class"] != "premium"
            or int(row["price_cents"]) <= 0 or not str(row["license"]).strip()
        ):
            raise ValueError("projeto não está elegível para pedido")
        return {
            "source_project_id": int(row["id"]),
            "source_project_version_id": row["current_version_id"],
            "seller_user_id": row["owner_user_id"],
            "title": str(row["title"]),
            "license": str(row["license"]),
            "terms": str(row["commercial_terms"]),
            "project_snapshot_json": json.dumps(dict(row), sort_keys=True, default=str),
            "unit_price_minor": int(row["price_cents"]),
            "quantity": quantity,
            "currency": str(row["currency"]).upper(),
        }

    @staticmethod
    def _insert_order(connection, public_id, buyer_user_id, payload, digest, currency, subtotal) -> int:
        cursor = connection.execute(
            """
            INSERT INTO commerce_orders (
                public_id, buyer_user_id, idempotency_key, command_digest, currency,
                subtotal_minor, fee_minor, tax_minor, total_minor, country_code
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                public_id, buyer_user_id, payload.idempotency_key, digest, currency,
                subtotal, subtotal, payload.country_code.upper(),
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _insert_item(connection, order_id: int, snapshot: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO commerce_order_items (
                order_id, source_project_id, source_project_version_id, seller_user_id,
                title_snapshot, license_snapshot, terms_snapshot, project_snapshot_json,
                unit_price_minor, quantity, currency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id, snapshot["source_project_id"], snapshot["source_project_version_id"],
                snapshot["seller_user_id"], snapshot["title"], snapshot["license"],
                snapshot["terms"], snapshot["project_snapshot_json"],
                snapshot["unit_price_minor"], snapshot["quantity"], snapshot["currency"],
            ),
        )

    @staticmethod
    def _load(connection, public_id: str, buyer_user_id: int) -> OrderResponse:
        order = connection.execute(
            "SELECT * FROM commerce_orders WHERE public_id = ? AND buyer_user_id = ?",
            (public_id, buyer_user_id),
        ).fetchone()
        if order is None:
            raise ValueError("pedido não encontrado")
        rows = connection.execute(
            "SELECT * FROM commerce_order_items WHERE order_id = ? ORDER BY id", (order["id"],)
        ).fetchall()
        return _order_response(order, rows)


def _order_digest(buyer_user_id: int, payload: OrderCreateRequest) -> str:
    encoded = json.dumps(
        {"buyer_user_id": buyer_user_id, **payload.model_dump()}, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _order_response(order, rows) -> OrderResponse:
    items = [
        OrderItemResponse(
            id=int(row["id"]), project_id=int(row["source_project_id"]),
            project_version_id=row["source_project_version_id"], title=str(row["title_snapshot"]),
            license=str(row["license_snapshot"]), terms=str(row["terms_snapshot"]),
            unit_price_minor=int(row["unit_price_minor"]), quantity=int(row["quantity"]),
            currency=str(row["currency"]),
        ) for row in rows
    ]
    return OrderResponse(
        public_id=str(order["public_id"]), buyer_user_id=int(order["buyer_user_id"]),
        status=str(order["status"]), currency=str(order["currency"]),
        subtotal_minor=int(order["subtotal_minor"]), fee_minor=int(order["fee_minor"]),
        tax_minor=int(order["tax_minor"]), total_minor=int(order["total_minor"]),
        country_code=str(order["country_code"]), tax_status=str(order["tax_status"]), items=items,
    )
