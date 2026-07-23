from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid

from app.database import connect_database
from app.finance_ledger import FinanceLedgerRepository
from app.modules.finance.contracts import PaymentCommandRequest, PaymentCommandResponse
from app.modules.finance.domain import LedgerAccount, LedgerCommand, LedgerEntry, Money


class FinancePaymentOperationsService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.ledger = FinanceLedgerRepository(database_path)

    def execute(
        self,
        payment_public_id: str,
        payload: PaymentCommandRequest,
        actor_user_id: int,
    ) -> PaymentCommandResponse:
        digest = _command_digest(payment_public_id, payload, actor_user_id)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM finance_payment_commands WHERE idempotency_key = ?",
                (payload.idempotency_key,),
            ).fetchone()
            if existing is not None:
                if existing["command_digest"] != digest:
                    raise ValueError("chave idempotente já usada com comando diferente")
                return _response(payment_public_id, existing, duplicate=True)
            intent = connection.execute(
                "SELECT * FROM payment_intents WHERE public_id = ?",
                (payment_public_id,),
            ).fetchone()
            if intent is None:
                raise ValueError("payment intent não encontrado")
            amount, result = self._validate(connection, intent, payload)
            command_id = self._insert_command(
                connection, intent, payload, digest, amount, result, actor_user_id
            )
            self._apply(connection, intent, payload, command_id, amount, actor_user_id)
            row = connection.execute(
                "SELECT * FROM finance_payment_commands WHERE id = ?", (command_id,)
            ).fetchone()
            return _response(payment_public_id, row)

    def _validate(self, connection, intent, payload: PaymentCommandRequest) -> tuple[int | None, str]:
        status = str(intent["status"])
        if payload.command == "capture":
            if status not in {"requires_action", "authorized"}:
                raise ValueError("pagamento não pode ser capturado neste estado")
            return int(intent["amount_minor"]), "captured"
        if payload.command == "cancel":
            if status not in {"requires_action", "authorized"}:
                raise ValueError("pagamento não pode ser cancelado neste estado")
            return None, "cancelled"
        if payload.command == "refund":
            return self._validate_refund(connection, intent, payload)
        if payload.command == "open_dispute":
            if status not in {"captured", "partially_refunded"}:
                raise ValueError("disputa exige pagamento capturado")
            return payload.amount_minor or self._remaining_amount(connection, intent), "disputed"
        if payload.command.startswith("resolve_dispute_"):
            dispute = self._open_dispute(connection, int(intent["id"]))
            return int(dispute["amount_minor"]), "won" if payload.command.endswith("won") else "lost"
        raise ValueError("comando financeiro inválido")

    def _validate_refund(self, connection, intent, payload) -> tuple[int, str]:
        if intent["status"] not in {"captured", "partially_refunded"}:
            raise ValueError("reembolso exige pagamento capturado")
        amount = payload.amount_minor or self._remaining_amount(connection, intent)
        remaining = self._remaining_amount(connection, intent)
        if amount <= 0 or amount > remaining:
            raise ValueError("reembolso excede valor elegível")
        return amount, "refunded" if amount == remaining else "partially_refunded"

    @staticmethod
    def _remaining_amount(connection, intent) -> int:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(amount_minor), 0) AS refunded
            FROM payment_refunds WHERE payment_intent_id = ?
            """,
            (intent["id"],),
        ).fetchone()
        return int(intent["amount_minor"]) - int(row["refunded"])

    @staticmethod
    def _open_dispute(connection, intent_id: int):
        row = connection.execute(
            "SELECT * FROM payment_disputes WHERE payment_intent_id = ? AND status = 'open'",
            (intent_id,),
        ).fetchone()
        if row is None:
            raise ValueError("nenhuma disputa aberta")
        return row

    @staticmethod
    def _insert_command(connection, intent, payload, digest, amount, result, actor_user_id) -> int:
        cursor = connection.execute(
            """
            INSERT INTO finance_payment_commands (
                payment_intent_id, command_type, idempotency_key, command_digest,
                amount_minor, result_status, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (intent["id"], payload.command, payload.idempotency_key, digest, amount, result, actor_user_id),
        )
        return int(cursor.lastrowid)

    def _apply(self, connection, intent, payload, command_id, amount, actor_user_id) -> None:
        if payload.command == "capture":
            self._capture(connection, intent, command_id, actor_user_id)
        elif payload.command == "cancel":
            self._set_states(connection, intent, "cancelled", "cancelled")
        elif payload.command == "refund":
            self._refund(connection, intent, payload, command_id, int(amount), actor_user_id)
        elif payload.command == "open_dispute":
            self._open(connection, intent, payload, command_id, int(amount), actor_user_id)
        else:
            self._resolve(connection, intent, payload, command_id, actor_user_id)

    def _capture(self, connection, intent, command_id: int, actor_user_id: int) -> None:
        amount = int(intent["amount_minor"])
        allocations = _order_allocations(connection, intent["order_id"], amount)
        entries = [_clearing_entry("debit", amount, str(intent["currency"]))]
        entries.extend(_payable_entries("credit", allocations, str(intent["currency"])))
        self.ledger.post_in_connection(
            connection,
            _ledger_command(intent, command_id, "payment_capture", entries, actor_user_id),
        )
        self._set_states(connection, intent, "captured", "paid")

    def _refund(self, connection, intent, payload, command_id, amount, actor_user_id) -> None:
        allocations = _order_allocations(connection, intent["order_id"], amount)
        public_id = f"ref_{uuid.uuid4().hex}"
        cursor = connection.execute(
            """
            INSERT INTO payment_refunds (
                public_id, payment_intent_id, order_id, amount_minor, currency,
                reason, status, command_id
            ) VALUES (?, ?, ?, ?, ?, ?, 'succeeded', ?)
            """,
            (public_id, intent["id"], intent["order_id"], amount, intent["currency"], payload.reason, command_id),
        )
        for seller_id, allocated in allocations:
            connection.execute(
                """
                INSERT INTO payment_refund_allocations (refund_id, seller_user_id, amount_minor, currency)
                VALUES (?, ?, ?, ?)
                """,
                (cursor.lastrowid, seller_id, allocated, intent["currency"]),
            )
        entries = _payable_entries("debit", allocations, str(intent["currency"]))
        entries.append(_clearing_entry("credit", amount, str(intent["currency"])))
        self.ledger.post_in_connection(
            connection, _ledger_command(intent, command_id, "payment_refund", entries, actor_user_id)
        )
        remaining = self._remaining_amount(connection, intent)
        target = "refunded" if remaining == 0 else "partially_refunded"
        self._set_states(connection, intent, target, target)

    def _open(self, connection, intent, payload, command_id, amount, actor_user_id) -> None:
        if connection.execute(
            "SELECT 1 FROM payment_disputes WHERE payment_intent_id = ? AND status = 'open'",
            (intent["id"],),
        ).fetchone():
            raise ValueError("já existe disputa aberta")
        connection.execute(
            """
            INSERT INTO payment_disputes (
                public_id, payment_intent_id, order_id, amount_minor, currency,
                reason_code, status, opened_command_id
            ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (f"dsp_{uuid.uuid4().hex}", intent["id"], intent["order_id"], amount,
             intent["currency"], payload.reason or "unspecified", command_id),
        )
        allocations = _order_allocations(connection, intent["order_id"], amount)
        entries = _payable_entries("debit", allocations, str(intent["currency"]))
        entries.append(_clearing_entry("credit", amount, str(intent["currency"])))
        self.ledger.post_in_connection(
            connection, _ledger_command(intent, command_id, "payment_dispute", entries, actor_user_id)
        )
        self._set_states(connection, intent, "disputed", "disputed")

    def _resolve(self, connection, intent, payload, command_id, actor_user_id) -> None:
        dispute = self._open_dispute(connection, int(intent["id"]))
        won = payload.command == "resolve_dispute_won"
        if won:
            allocations = _order_allocations(connection, intent["order_id"], int(dispute["amount_minor"]))
            entries = [_clearing_entry("debit", int(dispute["amount_minor"]), str(intent["currency"]))]
            entries.extend(_payable_entries("credit", allocations, str(intent["currency"])))
            self.ledger.post_in_connection(
                connection, _ledger_command(intent, command_id, "dispute_won", entries, actor_user_id)
            )
        connection.execute(
            """
            UPDATE payment_disputes SET status = ?, resolved_command_id = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'open'
            """,
            ("won" if won else "lost", command_id, dispute["id"]),
        )
        target = "captured" if won else "refunded"
        order_target = "paid" if won else "refunded"
        self._set_states(connection, intent, target, order_target)

    @staticmethod
    def _set_states(connection, intent, payment_status: str, order_status: str) -> None:
        connection.execute(
            "UPDATE payment_intents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payment_status, intent["id"]),
        )
        if intent["order_id"] is not None:
            connection.execute(
                "UPDATE commerce_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (order_status, intent["order_id"]),
            )


def _order_allocations(connection, order_id: int | None, amount: int) -> list[tuple[int | None, int]]:
    if order_id is None:
        return [(None, amount)]
    rows = connection.execute(
        """
        SELECT seller_user_id, SUM(unit_price_minor * quantity) AS gross
        FROM commerce_order_items WHERE order_id = ? GROUP BY seller_user_id ORDER BY seller_user_id
        """,
        (order_id,),
    ).fetchall()
    weights = [(row["seller_user_id"], int(row["gross"])) for row in rows]
    total = sum(weight for _seller, weight in weights)
    allocated = [(seller, amount * weight // total) for seller, weight in weights]
    remainder = amount - sum(value for _seller, value in allocated)
    for index in range(remainder):
        seller, value = allocated[index % len(allocated)]
        allocated[index % len(allocated)] = (seller, value + 1)
    return [(seller, value) for seller, value in allocated if value > 0]


def _payable_entries(side, allocations, currency) -> list[LedgerEntry]:
    return [
        LedgerEntry(
            LedgerAccount(f"creator_payable:{seller or 'platform'}:{currency}", "liability", currency, seller),
            side,
            Money(amount, currency),
        )
        for seller, amount in allocations
    ]


def _clearing_entry(side: str, amount: int, currency: str) -> LedgerEntry:
    return LedgerEntry(
        LedgerAccount(f"provider_clearing:{currency}", "asset", currency),
        side,  # type: ignore[arg-type]
        Money(amount, currency),
    )


def _ledger_command(intent, command_id, operation, entries, actor_user_id) -> LedgerCommand:
    return LedgerCommand(
        external_key=f"payment-command:{command_id}", operation_type=operation,
        correlation_id=f"payment:{intent['public_id']}", entries=tuple(entries),
        metadata={"payment_public_id": str(intent["public_id"]), "command_id": command_id},
        created_by_user_id=actor_user_id,
    )


def _command_digest(payment_public_id, payload, actor_user_id) -> str:
    encoded = json.dumps(
        {"payment_public_id": payment_public_id, "actor_user_id": actor_user_id, **payload.model_dump()},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _response(payment_public_id, row, duplicate: bool = False) -> PaymentCommandResponse:
    return PaymentCommandResponse(
        command_id=int(row["id"]), payment_public_id=payment_public_id,
        command=str(row["command_type"]), result_status=str(row["result_status"]),
        amount_minor=row["amount_minor"], duplicate=duplicate,
    )
