from __future__ import annotations

from decimal import Decimal

import pytest

from octaspace import MICRO_USD_PER_USD, format_usd, micro_usd_to_usd, usd_to_micro_usd


def test_format_usd() -> None:
    assert format_usd(100) == "$0.000100"
    assert format_usd(12_500_000) == "$12.500000"
    assert format_usd(-1_250_000) == "-$1.250000"
    with pytest.raises(TypeError):
        format_usd(1.5)  # type: ignore[arg-type]


def test_conversions() -> None:
    assert MICRO_USD_PER_USD == 1_000_000
    assert micro_usd_to_usd(250_000) == Decimal("0.25")
    assert usd_to_micro_usd("0.25") == 250_000
    assert usd_to_micro_usd(0.1) == 100_000
    assert usd_to_micro_usd(Decimal("1.0000005")) == 1_000_000
    with pytest.raises(ValueError):
        usd_to_micro_usd(float("inf"))
    with pytest.raises(ValueError):
        usd_to_micro_usd("abc")
