from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from app.database import connect_database
from app.modules.finance.domain import LedgerAccount, LedgerCommand


@dataclass(frozen=True)
class PostedLedgerTransaction:
    id: int
    external_key: str
    operation_type: str
    currency: str
    correlation_id: str
    entry_count: int


class FinanceLedgerRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def post(self, command: LedgerCommand) -> PostedLedgerTransaction:
        with connect_database(self.database_path) as connection:
            return self.post_in_connection(connection, command)

    def post_in_connection(self, connection, command: LedgerCommand) -> PostedLedgerTransaction:
        digest = _command_digest(command)
        existing = connection.execute(
            "SELECT id, command_digest FROM finance_ledger_transactions WHERE external_key = ?",
            (command.external_key,),
        ).fetchone()
        if existing is not None:
            if existing["command_digest"] != digest:
                raise ValueError("chave idempotente já usada com comando diferente")
            return self._load_posted(connection, int(existing["id"]))
        transaction_id = self._create_draft(connection, command, digest)
        for entry in command.entries:
            account_id = self._ensure_account(connection, entry.account)
            connection.execute(
                """
                INSERT INTO finance_ledger_entries (
                    transaction_id, account_id, side, amount_minor, currency
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (transaction_id, account_id, entry.side, entry.money.amount_minor, command.currency),
            )
        connection.execute(
            """
            UPDATE finance_ledger_transactions
            SET status = 'posted', posted_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'draft'
            """,
            (transaction_id,),
        )
        return self._load_posted(connection, transaction_id)

    def reconcile(self) -> dict[str, object]:
        with connect_database(self.database_path) as connection:
            imbalance = connection.execute(
                """
                SELECT COUNT(*) AS total FROM (
                    SELECT transaction_id
                    FROM finance_ledger_entries
                    GROUP BY transaction_id
                    HAVING SUM(CASE WHEN side = 'debit' THEN amount_minor ELSE -amount_minor END) <> 0
                ) invalid
                """
            ).fetchone()
            draft = connection.execute(
                "SELECT COUNT(*) AS total FROM finance_ledger_transactions WHERE status = 'draft'"
            ).fetchone()
            posted = connection.execute(
                "SELECT COUNT(*) AS total FROM finance_ledger_transactions WHERE status = 'posted'"
            ).fetchone()
        return {
            "status": "passed" if int(imbalance["total"]) == 0 and int(draft["total"]) == 0 else "blocked",
            "imbalanced_transactions": int(imbalance["total"]),
            "draft_transactions": int(draft["total"]),
            "posted_transactions": int(posted["total"]),
        }

    @staticmethod
    def _create_draft(connection, command: LedgerCommand, digest: str) -> int:
        cursor = connection.execute(
            """
            INSERT INTO finance_ledger_transactions (
                external_key, command_digest, operation_type, currency,
                correlation_id, metadata_json, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                command.external_key,
                digest,
                command.operation_type,
                command.currency,
                command.correlation_id,
                json.dumps(command.metadata, sort_keys=True, separators=(",", ":")),
                command.created_by_user_id,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _ensure_account(connection, account: LedgerAccount) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO finance_accounts (
                code, account_type, currency, owner_user_id
            ) VALUES (?, ?, ?, ?)
            """,
            (account.code, account.account_type, account.currency, account.owner_user_id),
        )
        row = connection.execute(
            """
            SELECT id, account_type, currency, owner_user_id, is_active
            FROM finance_accounts WHERE code = ?
            """,
            (account.code,),
        ).fetchone()
        expected = (account.account_type, account.currency, account.owner_user_id)
        actual = (row["account_type"], row["currency"], row["owner_user_id"])
        if actual != expected or not bool(row["is_active"]):
            raise ValueError("conta existente diverge do contrato solicitado")
        return int(row["id"])

    @staticmethod
    def _load_posted(connection, transaction_id: int) -> PostedLedgerTransaction:
        row = connection.execute(
            """
            SELECT transaction_row.*, COUNT(entry_row.id) AS entry_count
            FROM finance_ledger_transactions transaction_row
            JOIN finance_ledger_entries entry_row ON entry_row.transaction_id = transaction_row.id
            WHERE transaction_row.id = ? AND transaction_row.status = 'posted'
            GROUP BY transaction_row.id
            """,
            (transaction_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("transação não foi postada")
        return PostedLedgerTransaction(
            id=int(row["id"]),
            external_key=str(row["external_key"]),
            operation_type=str(row["operation_type"]),
            currency=str(row["currency"]),
            correlation_id=str(row["correlation_id"]),
            entry_count=int(row["entry_count"]),
        )


def _command_digest(command: LedgerCommand) -> str:
    payload = {
        "external_key": command.external_key,
        "operation_type": command.operation_type,
        "correlation_id": command.correlation_id,
        "entries": [asdict(entry) for entry in command.entries],
        "metadata": command.metadata,
        "created_by_user_id": command.created_by_user_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
