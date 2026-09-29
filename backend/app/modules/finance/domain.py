from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AccountType = Literal["asset", "liability", "equity", "revenue", "expense"]
EntrySide = Literal["debit", "credit"]
PaymentStatus = Literal[
    "requires_action",
    "authorized",
    "captured",
    "cancelled",
    "partially_refunded",
    "refunded",
    "disputed",
    "failed",
]


def normalize_currency(value: str) -> str:
    currency = value.strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("moeda deve usar código ISO de três letras")
    return currency


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise TypeError("dinheiro deve usar unidade monetária mínima inteira")
        if self.amount_minor < 0:
            raise ValueError("valor monetário não pode ser negativo")
        object.__setattr__(self, "currency", normalize_currency(self.currency))


@dataclass(frozen=True)
class LedgerAccount:
    code: str
    account_type: AccountType
    currency: str
    owner_user_id: int | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("código da conta é obrigatório")
        object.__setattr__(self, "code", self.code.strip())
        object.__setattr__(self, "currency", normalize_currency(self.currency))


@dataclass(frozen=True)
class LedgerEntry:
    account: LedgerAccount
    side: EntrySide
    money: Money

    def __post_init__(self) -> None:
        if self.money.amount_minor <= 0:
            raise ValueError("lançamento deve ser positivo")
        if self.account.currency != self.money.currency:
            raise ValueError("conta e lançamento devem usar a mesma moeda")


@dataclass(frozen=True)
class LedgerCommand:
    external_key: str
    operation_type: str
    correlation_id: str
    entries: tuple[LedgerEntry, ...]
    metadata: dict[str, object]
    created_by_user_id: int | None = None

    def __post_init__(self) -> None:
        if not self.external_key.strip() or not self.operation_type.strip():
            raise ValueError("chave externa e tipo da operação são obrigatórios")
        if not self.correlation_id.strip():
            raise ValueError("correlation id é obrigatório")
        validate_balanced_entries(self.entries)
        reject_non_integer_money(self.metadata)

    @property
    def currency(self) -> str:
        return self.entries[0].money.currency


def validate_balanced_entries(entries: tuple[LedgerEntry, ...]) -> None:
    if len(entries) < 2:
        raise ValueError("transação exige ao menos dois lançamentos")
    currencies = {entry.money.currency for entry in entries}
    if len(currencies) != 1:
        raise ValueError("transação não pode misturar moedas")
    debit = sum(entry.money.amount_minor for entry in entries if entry.side == "debit")
    credit = sum(entry.money.amount_minor for entry in entries if entry.side == "credit")
    if debit != credit:
        raise ValueError("soma de débitos e créditos deve ser zero")


def reject_non_integer_money(value: object, path: str = "metadata") -> None:
    if isinstance(value, float):
        raise TypeError(f"float não é permitido em {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            reject_non_integer_money(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            reject_non_integer_money(child, f"{path}[{index}]")


PAYMENT_TRANSITIONS: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    "requires_action": frozenset({"authorized", "captured", "cancelled", "failed"}),
    "authorized": frozenset({"captured", "cancelled", "failed"}),
    "captured": frozenset({"partially_refunded", "refunded", "disputed"}),
    "partially_refunded": frozenset({"partially_refunded", "refunded", "disputed"}),
    "disputed": frozenset({"captured", "partially_refunded", "refunded"}),
    "cancelled": frozenset(),
    "refunded": frozenset(),
    "failed": frozenset(),
}


def validate_payment_transition(current: PaymentStatus, target: PaymentStatus) -> None:
    if target == current:
        return
    if target not in PAYMENT_TRANSITIONS[current]:
        raise ValueError(f"transição de pagamento inválida: {current} -> {target}")
