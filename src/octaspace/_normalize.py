"""Clean-up of response values that stand for "unknown"."""

from __future__ import annotations

from datetime import datetime
from typing import Any

_GPU_INTEGER_FIELDS = (
    "mem_total_mb",
    "pcie_link_gen",
    "pcie_link_width",
    "core_clock",
    "mem_clock",
    "power_limit",
)


def null_strings(value: Any) -> Any:
    """Replace every ``"null"`` string value (not key) with ``None``, in place.

    Never apply it where ``"null"`` can be data, such as a session's ``envs``.
    """
    if value == "null":
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = null_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            value[key] = null_strings(item)
    return value


def machines(items: Any) -> Any:
    """Normalize a machine listing: ``"null"`` → ``None``, GPU integers given as strings → int."""
    null_strings(items)
    for machine in items if isinstance(items, list) else []:
        gpus = machine.get("gpus") if isinstance(machine, dict) else None
        for gpu in gpus if isinstance(gpus, list) else []:
            if not isinstance(gpu, dict):
                continue
            for field in _GPU_INTEGER_FIELDS:
                value = gpu.get(field)
                if isinstance(value, str):
                    gpu[field] = _to_int(value)
    return items


def apps(items: Any) -> Any:
    """``"null"`` → ``None`` in ``category`` and ``description`` only."""
    for app in items if isinstance(items, list) else []:
        if isinstance(app, dict):
            for field in ("category", "description"):
                if app.get(field) == "null":
                    app[field] = None
    return items


def unix_seconds(value: int | float | datetime | None) -> int | None:
    """Unix seconds from a number or a ``datetime``; ``None`` stays ``None``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"Expected Unix seconds or a datetime, got {value!r}")
    return int(value)


def _to_int(value: str) -> int | None:
    try:
        return int(float(value.strip()))
    except (ValueError, OverflowError):
        return None
