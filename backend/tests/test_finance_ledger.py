from pathlib import Path

import pytest

from app.database import connect_database, initialize_database
from app.finance_ledger import FinanceLedgerRepository
from app.modules.finance.domain import (
    LedgerAccount,
    LedgerCommand,
    LedgerEntry,
    Money,
)


def command(amount: int = 1250, external_key: str = "payment:one") -> LedgerCommand:
    return LedgerCommand(
        external_key=external_key,
        operation_type="payment_capture",
        correlation_id="corr-finance-1",
        entries=(
            LedgerEntry(
                LedgerAccount("provider_clearing:BRL", "asset", "BRL"),
                "debit",
                Money(amount, "BRL"),
            ),
            LedgerEntry(
                LedgerAccount("sales_revenue:BRL", "revenue", "BRL"),
                "credit",
                Money(amount, "BRL"),
            ),
        ),
        metadata={"order_reference": "ord_1", "amount_minor": amount},
    )


def test_posts_balanced_transaction_and_replay_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = FinanceLedgerRepository(database_path)

    first = repository.post(command())
    replay = repository.post(command())

    assert replay == first
    assert first.entry_count == 2
    assert repository.reconcile() == {
        "status": "passed",
        "imbalanced_transactions": 0,
        "draft_transactions": 0,
        "posted_transactions": 1,
    }


def test_rejects_unbalanced_mixed_currency_and_float_money() -> None:
    with pytest.raises(ValueError, match="débitos e créditos"):
        LedgerCommand(
            external_key="bad",
            operation_type="bad",
            correlation_id="corr",
            entries=(
                LedgerEntry(LedgerAccount("cash", "asset", "BRL"), "debit", Money(10, "BRL")),
                LedgerEntry(LedgerAccount("revenue", "revenue", "BRL"), "credit", Money(9, "BRL")),
            ),
            metadata={},
        )
    with pytest.raises(ValueError, match="misturar moedas"):
        LedgerCommand(
            external_key="bad-currency",
            operation_type="bad",
            correlation_id="corr",
            entries=(
                LedgerEntry(LedgerAccount("cash-brl", "asset", "BRL"), "debit", Money(10, "BRL")),
                LedgerEntry(LedgerAccount("cash-usd", "asset", "USD"), "credit", Money(10, "USD")),
            ),
            metadata={},
        )
    with pytest.raises(TypeError, match="float"):
        command_with_metadata({"amount": 1.25})


def test_posted_rows_are_immutable_and_database_rejects_imbalance(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    posted = FinanceLedgerRepository(database_path).post(command())

    with pytest.raises(Exception, match="immutable"):
        with connect_database(database_path) as connection:
            connection.execute(
                "UPDATE finance_ledger_entries SET amount_minor = 1 WHERE transaction_id = ?",
                (posted.id,),
            )
    with pytest.raises(Exception, match="cannot be deleted"):
        with connect_database(database_path) as connection:
            connection.execute("DELETE FROM finance_ledger_transactions WHERE id = ?", (posted.id,))

    with pytest.raises(Exception, match="not balanced"):
        with connect_database(database_path) as connection:
            draft_id = connection.execute(
                """
                INSERT INTO finance_ledger_transactions (
                    external_key, command_digest, operation_type, currency, correlation_id
                ) VALUES ('bad-direct', 'digest', 'test', 'BRL', 'corr')
                """
            ).lastrowid
            account_id = connection.execute(
                """
                INSERT INTO finance_accounts (code, account_type, currency)
                VALUES ('bad-direct-account', 'asset', 'BRL')
                """
            ).lastrowid
            connection.execute(
                """
                INSERT INTO finance_ledger_entries (
                    transaction_id, account_id, side, amount_minor, currency
                ) VALUES (?, ?, 'debit', 10, 'BRL')
                """,
                (draft_id, account_id),
            )
            connection.execute(
                """
                INSERT INTO finance_ledger_entries (
                    transaction_id, account_id, side, amount_minor, currency
                ) VALUES (?, ?, 'credit', 9, 'BRL')
                """,
                (draft_id, account_id),
            )
            connection.execute(
                "UPDATE finance_ledger_transactions SET status = 'posted' WHERE id = ?",
                (draft_id,),
            )


def test_same_key_with_changed_command_is_rejected(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    repository = FinanceLedgerRepository(database_path)
    repository.post(command())

    with pytest.raises(ValueError, match="comando diferente"):
        repository.post(command(amount=1300))


def command_with_metadata(metadata: dict[str, object]) -> LedgerCommand:
    base = command()
    return LedgerCommand(
        external_key=base.external_key,
        operation_type=base.operation_type,
        correlation_id=base.correlation_id,
        entries=base.entries,
        metadata=metadata,
    )
