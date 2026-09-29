from __future__ import annotations

from pathlib import Path

from app.database import connect_database


class FinanceAdminQueryService:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def overview(self) -> dict[str, object]:
        with connect_database(self.database_path) as connection:
            return {
                "counts": self._counts(connection),
                "orders": self._rows(connection, "commerce_orders", "public_id, status, currency, total_minor, created_at"),
                "payments": self._rows(connection, "payment_intents", "public_id, status, currency, amount_minor, updated_at"),
                "ledger": self._rows(connection, "finance_ledger_transactions", "external_key, operation_type, currency, status, posted_at"),
                "disputes": self._rows(connection, "payment_disputes", "public_id, status, currency, amount_minor, created_at"),
                "payouts": self._rows(connection, "finance_payouts", "public_id, status, currency, amount_minor, created_at"),
                "reconciliations": self._rows(connection, "finance_reconciliation_runs", "public_id, status, currency, difference_minor, created_at"),
            }

    @staticmethod
    def _counts(connection) -> dict[str, int]:
        tables = {
            "orders": "commerce_orders",
            "payments": "payment_intents",
            "ledger_transactions": "finance_ledger_transactions",
            "open_disputes": "payment_disputes",
            "pending_payouts": "finance_payouts",
            "risk_review": "finance_risk_cases",
        }
        counts: dict[str, int] = {}
        for key, table in tables.items():
            suffix = " WHERE status = 'open'" if key == "open_disputes" else ""
            suffix = " WHERE status IN ('requested', 'approved', 'blocked')" if key == "pending_payouts" else suffix
            suffix = " WHERE status IN ('review_required', 'appealed')" if key == "risk_review" else suffix
            row = connection.execute(f"SELECT COUNT(*) AS total FROM {table}{suffix}").fetchone()
            counts[key] = int(row["total"])
        return counts

    @staticmethod
    def _rows(connection, table: str, columns: str) -> list[dict[str, object]]:
        rows = connection.execute(f"SELECT {columns} FROM {table} ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(row) for row in rows]
