from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from .. import _normalize
from ..types import (
    GpuCurrent,
    GpuHistory,
    GpuHistoryPoint,
    GpuLocation,
    GpuModelHistory,
    GpuPricePercentiles,
    GpuVerifiedFilter,
    MiningRole,
    MiningUsage,
)
from .base import Resource


class StatsResource(Resource):
    """GPU market and mining statistics; no API key needed."""

    def gpu_current(self, *, verified: GpuVerifiedFilter | None = None) -> GpuCurrent:
        """Return the GPU models on the market now (``GET /stats/gpu/current``).

        Per model: the number of GPUs (not nodes), how many are rented,
        performance, and price percentiles in micro-USD per GPU-hour.

        Args:
            verified: ``"all"`` (default), ``"yes"`` (verified nodes only) or ``"no"``.
        """
        params = {"verified": verified}
        data = self._request("GET", "/stats/gpu/current", params=params, auth="none")
        return cast(GpuCurrent, _normalize.null_strings(data))

    def gpu_history(
        self,
        *,
        gpu_name: str | Sequence[str] | None = None,
        verified: GpuVerifiedFilter | None = None,
        start: int | float | datetime | None = None,
        end: int | float | datetime | None = None,
        step: int | None = None,
    ) -> GpuHistory:
        """Return the GPU market over time by model (``GET /stats/gpu/history``).

        Turn one model's history into one dict per point with
        ``octaspace.gpu_history_points()``.

        Args:
            gpu_name: GPU model names, for example ``"NVIDIA GeForce RTX 4090"``;
                all models by default.
            verified: ``"all"`` (default), ``"yes"`` or ``"no"``.
            start: Unix seconds or a ``datetime``; the last day by default.
            end: Unix seconds or a ``datetime``.
            step: Seconds between points, at least 300 (3600 by default); a
                range has at most 2000 points.

        Raises:
            ValidationError: The range is invalid.
        """
        names = gpu_name if isinstance(gpu_name, str) or gpu_name is None else ",".join(gpu_name)
        params: dict[str, Any] = {
            "gpu_name": names,
            "verified": verified,
            "start": _normalize.unix_seconds(start),
            "end": _normalize.unix_seconds(end),
            "step": step,
        }
        data = self._request("GET", "/stats/gpu/history", params=params, auth="none")
        return cast(GpuHistory, _normalize.null_strings(data))

    def gpu_locations(self) -> list[GpuLocation]:
        """Return the number of GPUs by city and model (``GET /stats/gpu/locations``)."""
        data = self._request("GET", "/stats/gpu/locations", auth="none")
        return cast("list[GpuLocation]", _normalize.null_strings(data))

    def mining(self, *, role: MiningRole | None = None, days: int | None = None) -> MiningUsage:
        """Return what the platform's mining sessions run (``GET /stats/mining``).

        Miners, algorithms and pools, most used first, and the miners per day.

        Args:
            role: ``"gpu"`` (default) or ``"cpu"``.
            days: Days back, today included: 1 to 365 (30 by default).

        Raises:
            ValidationError: ``days`` is out of range.
        """
        params = {"role": role, "days": days}
        data = self._request("GET", "/stats/mining", params=params, auth="none")
        return cast(MiningUsage, _normalize.null_strings(data))


def _percentiles(series: Any, index: int) -> GpuPricePercentiles:
    def at(name: str) -> int | None:
        values = series.get(name) if isinstance(series, dict) else None
        if isinstance(values, list) and index < len(values):
            return cast("int | None", values[index])
        return None

    return {
        "p10": at("p10"),
        "p25": at("p25"),
        "p50": at("p50"),
        "p75": at("p75"),
        "p90": at("p90"),
    }


def gpu_history_points(history: GpuModelHistory) -> list[GpuHistoryPoint]:
    """Turn one model's history into one dict per timestamp.

    For example ``gpu_history_points(history["NVIDIA GeForce RTX 4090"])``.
    """
    supply: Any = history.get("supply_demand") or {}

    def count(name: str, index: int) -> int | None:
        values = supply.get(name)
        if isinstance(values, list) and index < len(values):
            return cast("int | None", values[index])
        return None

    return [
        {
            "ts": ts,
            "total": count("total", i),
            "available": count("available", i),
            "rented": count("rented", i),
            "available_price": _percentiles(history.get("available_price"), i),
            "rented_price": _percentiles(history.get("rented_price"), i),
        }
        for i, ts in enumerate(history.get("timestamps", []))
    ]
