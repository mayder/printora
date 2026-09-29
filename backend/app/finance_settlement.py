from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid

from app.database import connect_database
from app.finance_ledger import FinanceLedgerRepository
from app.modules.finance.contracts import (
    ClosingResponse,
    FinanceBalanceResponse,
    PayoutResponse,
    ReconciliationResponse,
)
from app.modules.finance.domain import LedgerAccount, LedgerCommand, LedgerEntry, Money, normalize_currency


NEGATIVE_POLICY = "saldo negativo compensa ganhos futuros e bloqueia repasse"


class FinanceSettlementService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.ledger = FinanceLedgerRepository(database_path)

    def balance(self, seller_user_id: int, currency: str) -> FinanceBalanceResponse:
        currency = normalize_currency(currency)
        with connect_database(self.database_path) as connection:
            ledger = _account_balance(connection, seller_user_id, currency)
            reserved = _reserved_balance(connection, seller_user_id, currency)
        return FinanceBalanceResponse(
            seller_user_id=seller_user_id, currency=currency, ledger_balance_minor=ledger,
            reserved_minor=reserved, available_minor=ledger - reserved,
            negative_balance_policy=NEGATIVE_POLICY,
        )

    def reconcile(
        self, currency: str, provider_reported_minor: int, evidence_reference: str, actor_user_id: int
    ) -> ReconciliationResponse:
        currency = normalize_currency(currency)
        if provider_reported_minor < 0:
            raise ValueError("saldo reportado pelo provedor não pode ser negativo")
        with connect_database(self.database_path) as connection:
            ledger = _clearing_balance(connection, currency)
            difference = provider_reported_minor - ledger
            status = "passed" if difference == 0 else "blocked"
            public_id = f"rec_{uuid.uuid4().hex}"
            evidence = hashlib.sha256(evidence_reference.strip().encode()).hexdigest()
            connection.execute(
                """
                INSERT INTO finance_reconciliation_runs (
                    public_id, provider, currency, ledger_clearing_minor,
                    provider_reported_minor, difference_minor, status,
                    evidence_sha256, executed_by_user_id
                ) VALUES (?, 'sandbox', ?, ?, ?, ?, ?, ?, ?)
                """,
                (public_id, currency, ledger, provider_reported_minor, difference, status, evidence, actor_user_id),
            )
        return ReconciliationResponse(
            public_id=public_id, currency=currency, ledger_clearing_minor=ledger,
            provider_reported_minor=provider_reported_minor, difference_minor=difference, status=status,
        )

    def request_payout(
        self, seller_user_id: int, currency: str, amount_minor: int, idempotency_key: str
    ) -> PayoutResponse:
        currency = normalize_currency(currency)
        digest = _payout_digest(seller_user_id, currency, amount_minor, idempotency_key)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM finance_payouts WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                if existing["command_digest"] != digest:
                    raise ValueError("chave idempotente já usada com repasse diferente")
                return _payout_response(existing)
            available = _account_balance(connection, seller_user_id, currency) - _reserved_balance(
                connection, seller_user_id, currency
            )
            if amount_minor <= 0 or amount_minor > available:
                raise ValueError("repasse excede saldo disponível")
            public_id = f"pot_{uuid.uuid4().hex}"
            connection.execute(
                """
                INSERT INTO finance_payouts (
                    public_id, seller_user_id, currency, amount_minor, status,
                    idempotency_key, command_digest, requested_by_user_id
                ) VALUES (?, ?, ?, ?, 'requested', ?, ?, ?)
                """,
                (public_id, seller_user_id, currency, amount_minor, idempotency_key, digest, seller_user_id),
            )
            row = connection.execute("SELECT * FROM finance_payouts WHERE public_id = ?", (public_id,)).fetchone()
        return _payout_response(row)

    def approve_payout(self, public_id: str, approver_user_id: int) -> PayoutResponse:
        with connect_database(self.database_path) as connection:
            row = _payout(connection, public_id)
            if row["status"] != "requested":
                raise ValueError("repasse não aguarda aprovação")
            if int(row["requested_by_user_id"]) == approver_user_id:
                raise PermissionError("solicitante não pode aprovar o próprio repasse")
            connection.execute(
                """
                UPDATE finance_payouts SET status = 'approved', approved_by_user_id = ?,
                    approved_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'requested'
                """,
                (approver_user_id, row["id"]),
            )
            return _payout_response(_payout(connection, public_id))

    def execute_payout(self, public_id: str, actor_user_id: int) -> PayoutResponse:
        with connect_database(self.database_path) as connection:
            row = _payout(connection, public_id)
            if row["status"] != "approved":
                raise ValueError("repasse não está aprovado")
            if int(row["approved_by_user_id"]) == actor_user_id:
                raise PermissionError("aprovador não pode executar o próprio repasse")
            reconciliation = _latest_reconciliation(connection, str(row["currency"]))
            if reconciliation is None or reconciliation["status"] != "passed":
                raise ValueError("reconciliação divergente bloqueia repasse")
            if _seller_has_open_dispute(connection, int(row["seller_user_id"])):
                raise ValueError("disputa aberta bloqueia repasse")
            transaction = self.ledger.post_in_connection(
                connection, _payout_ledger_command(row, actor_user_id)
            )
            connection.execute(
                """
                UPDATE finance_payouts SET status = 'paid', paid_ledger_transaction_id = ?,
                    reconciliation_run_id = ?, paid_by_user_id = ?, paid_at = CURRENT_TIMESTAMP WHERE id = ?
                """,
                (transaction.id, reconciliation["id"], actor_user_id, row["id"]),
            )
            return _payout_response(_payout(connection, public_id))

    def close(self, currency: str, period_key: str, actor_user_id: int) -> ClosingResponse:
        currency = normalize_currency(currency)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM finance_closings WHERE currency = ? AND period_key = ?",
                (currency, period_key),
            ).fetchone()
            if existing is not None:
                return _closing_response(existing)
            reconciliation = _latest_reconciliation(connection, currency)
            if reconciliation is None:
                raise ValueError("fechamento exige reconciliação")
            metrics = _closing_metrics(connection, currency)
            current_clearing = _clearing_balance(connection, currency)
            reconciled_current = current_clearing == int(reconciliation["ledger_clearing_minor"])
            status = (
                "closed"
                if reconciliation["status"] == "passed" and metrics[1] == 0 and reconciled_current
                else "blocked"
            )
            public_id = f"cls_{uuid.uuid4().hex}"
            connection.execute(
                """
                INSERT INTO finance_closings (
                    public_id, currency, period_key, reconciliation_run_id,
                    ledger_transaction_count, ledger_imbalance_count,
                    open_dispute_count, status, closed_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (public_id, currency, period_key, reconciliation["id"], *metrics, status, actor_user_id),
            )
            row = connection.execute("SELECT * FROM finance_closings WHERE public_id = ?", (public_id,)).fetchone()
        return _closing_response(row)


def _account_balance(connection, seller_user_id: int, currency: str) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN entry.side = 'credit' THEN entry.amount_minor ELSE -entry.amount_minor END), 0) AS amount
        FROM finance_accounts account
        LEFT JOIN finance_ledger_entries entry ON entry.account_id = account.id
        WHERE account.owner_user_id = ? AND account.currency = ? AND account.code LIKE 'creator_payable:%'
        """,
        (seller_user_id, currency),
    ).fetchone()
    return int(row["amount"])


def _clearing_balance(connection, currency: str) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN entry.side = 'debit' THEN entry.amount_minor ELSE -entry.amount_minor END), 0) AS amount
        FROM finance_accounts account
        LEFT JOIN finance_ledger_entries entry ON entry.account_id = account.id
        WHERE account.code = ?
        """,
        (f"provider_clearing:{currency}",),
    ).fetchone()
    return int(row["amount"])


def _reserved_balance(connection, seller_user_id: int, currency: str) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(SUM(amount_minor), 0) AS amount FROM finance_payouts
        WHERE seller_user_id = ? AND currency = ? AND status IN ('requested', 'approved')
        """,
        (seller_user_id, currency),
    ).fetchone()
    return int(row["amount"])


def _seller_has_open_dispute(connection, seller_user_id: int) -> bool:
    row = connection.execute(
        """
        SELECT 1 FROM payment_disputes dispute
        JOIN commerce_order_items item ON item.order_id = dispute.order_id
        WHERE item.seller_user_id = ? AND dispute.status = 'open' LIMIT 1
        """,
        (seller_user_id,),
    ).fetchone()
    return row is not None


def _latest_reconciliation(connection, currency: str):
    return connection.execute(
        "SELECT * FROM finance_reconciliation_runs WHERE currency = ? ORDER BY id DESC LIMIT 1",
        (currency,),
    ).fetchone()


def _payout(connection, public_id: str):
    row = connection.execute("SELECT * FROM finance_payouts WHERE public_id = ?", (public_id,)).fetchone()
    if row is None:
        raise ValueError("repasse não encontrado")
    return row


def _closing_metrics(connection, currency: str) -> tuple[int, int, int]:
    transactions = connection.execute(
        "SELECT COUNT(*) AS total FROM finance_ledger_transactions WHERE currency = ? AND status = 'posted'",
        (currency,),
    ).fetchone()
    imbalance = connection.execute(
        """
        SELECT COUNT(*) AS total FROM (
            SELECT transaction_id FROM finance_ledger_entries WHERE currency = ?
            GROUP BY transaction_id
            HAVING SUM(CASE WHEN side = 'debit' THEN amount_minor ELSE -amount_minor END) <> 0
        ) invalid
        """,
        (currency,),
    ).fetchone()
    disputes = connection.execute(
        "SELECT COUNT(*) AS total FROM payment_disputes WHERE currency = ? AND status = 'open'",
        (currency,),
    ).fetchone()
    return int(transactions["total"]), int(imbalance["total"]), int(disputes["total"])


def _payout_ledger_command(row, actor_user_id: int) -> LedgerCommand:
    currency, amount = str(row["currency"]), int(row["amount_minor"])
    return LedgerCommand(
        external_key=f"payout:{row['public_id']}", operation_type="payout",
        correlation_id=f"payout:{row['public_id']}",
        entries=(
            LedgerEntry(
                LedgerAccount(f"creator_payable:{row['seller_user_id']}:{currency}", "liability", currency, int(row["seller_user_id"])),
                "debit", Money(amount, currency),
            ),
            LedgerEntry(LedgerAccount(f"provider_clearing:{currency}", "asset", currency), "credit", Money(amount, currency)),
        ), metadata={"payout_public_id": str(row["public_id"])}, created_by_user_id=actor_user_id,
    )


def _payout_digest(seller_user_id, currency, amount_minor, idempotency_key) -> str:
    payload = {"seller": seller_user_id, "currency": currency, "amount": amount_minor, "key": idempotency_key}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _payout_response(row) -> PayoutResponse:
    return PayoutResponse(
        public_id=str(row["public_id"]), seller_user_id=int(row["seller_user_id"]),
        currency=str(row["currency"]), amount_minor=int(row["amount_minor"]), status=str(row["status"]),
        requested_by_user_id=int(row["requested_by_user_id"]), approved_by_user_id=row["approved_by_user_id"],
    )


def _closing_response(row) -> ClosingResponse:
    return ClosingResponse(
        public_id=str(row["public_id"]), currency=str(row["currency"]), period_key=str(row["period_key"]),
        status=str(row["status"]), ledger_transaction_count=int(row["ledger_transaction_count"]),
        ledger_imbalance_count=int(row["ledger_imbalance_count"]), open_dispute_count=int(row["open_dispute_count"]),
    )
