from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Account:
    """An account profile, built from ``accounts.profile().data``."""

    account_uuid: str
    email: str
    avatar: str | None
    balance: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Account:
        return cls(
            account_uuid=str(data["account_uuid"]),
            email=str(data["email"]),
            avatar=data.get("avatar"),
            balance=float(data["balance"]) if data.get("balance") is not None else None,
        )


@dataclass(frozen=True, slots=True)
class Balance:
    """An account balance, built from ``accounts.balance().data``."""

    amount: float
    currency: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Balance:
        amount = data.get("amount", data.get("balance", 0))
        return cls(amount=float(amount), currency=str(data.get("currency", "OCTA")))
