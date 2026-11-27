"""Money helpers: the API gives amounts as integer micro-USD (``1`` = $0.000001)."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

MICRO_USD_PER_USD = 1_000_000
"""Number of micro-USD in one dollar."""


def micro_usd_to_usd(amount: int) -> Decimal:
    """Convert micro-USD to dollars exactly.

    ``micro_usd_to_usd(250000)`` is ``Decimal("0.250000")``.
    """
    _check_int(amount)
    return Decimal(amount).scaleb(-6)


def usd_to_micro_usd(usd: Decimal | int | float | str) -> int:
    """Convert dollars to micro-USD, rounded to the nearest integer.

    Use it for ``hosting.set_prices()``: ``usd_to_micro_usd("0.25")`` is ``250000``.
    Pass a ``Decimal`` or a string for an exact value.

    Raises:
        ValueError: The amount is not a finite number.
    """
    try:
        value = Decimal(str(usd)) if isinstance(usd, float) else Decimal(usd)
    except InvalidOperation:
        raise ValueError(f"Not a dollar amount: {usd!r}") from None
    if not value.is_finite():
        raise ValueError(f"Not a finite dollar amount: {usd!r}")
    return int((value * MICRO_USD_PER_USD).to_integral_value(rounding=ROUND_HALF_EVEN))


def format_usd(amount: int) -> str:
    """Format micro-USD as dollars with six decimals: ``-1250000`` → ``"-$1.250000"``."""
    _check_int(amount)
    sign = "-" if amount < 0 else ""
    whole, fraction = divmod(abs(amount), MICRO_USD_PER_USD)
    return f"{sign}${whole}.{fraction:06d}"


def _check_int(amount: int) -> None:
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError(f"Not a micro-USD integer: {amount!r}")


__all__ = ["MICRO_USD_PER_USD", "format_usd", "micro_usd_to_usd", "usd_to_micro_usd"]
