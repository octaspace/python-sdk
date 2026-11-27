from __future__ import annotations

from datetime import datetime
from typing import cast

from .. import _normalize
from ..types import NetworkHistory, NetworkHistoryPoint, NetworkInfo
from .base import Resource


class NetworkResource(Resource):
    """Platform statistics; no API key needed."""

    def info(self) -> NetworkInfo:
        """Return platform statistics now (``GET /network``).

        Nodes, capacity, sessions, users, rendered frames and VPN nodes.
        """
        data = self._request("GET", "/network", auth="none")
        return cast(NetworkInfo, _normalize.null_strings(data))

    def history(
        self,
        *,
        start: int | float | datetime | None = None,
        end: int | float | datetime | None = None,
        step: int | None = None,
    ) -> NetworkHistory:
        """Return platform statistics over time (``GET /network/history``).

        Parallel lists, a point per ``step``; each value is the average over
        its step, so it can be fractional. Turn them into one dict per point
        with ``octaspace.network_history_points()``.

        Args:
            start: Unix seconds or a ``datetime``; a day before ``end`` by default.
            end: Unix seconds or a ``datetime``; now by default.
            step: Seconds between points, at least 300 (3600 by default); a
                range has at most 2000 points.

        Raises:
            ValidationError: The range is invalid (``step`` under 300, too
                many points, ``start`` after ``end``).
        """
        params = {
            "start": _normalize.unix_seconds(start),
            "end": _normalize.unix_seconds(end),
            "step": step,
        }
        data = self._request("GET", "/network/history", params=params, auth="none")
        return cast(NetworkHistory, _normalize.null_strings(data))


def network_history_points(history: NetworkHistory) -> list[NetworkHistoryPoint]:
    """Turn the parallel lists of ``network.history()`` into one dict per timestamp."""

    def at(name: str, index: int) -> float | None:
        values = history.get(name)
        if isinstance(values, list) and index < len(values):
            return cast("float | None", values[index])
        return None

    return [
        {
            "ts": ts,
            "nodes_online": at("nodes_online", i),
            "nodes_available": at("nodes_available", i),
            "nodes_rented": at("nodes_rented", i),
            "countries": at("countries", i),
            "gpus": at("gpus", i),
            "gpus_rented": at("gpus_rented", i),
            "tflops": at("tflops", i),
            "vpn_nodes": at("vpn_nodes", i),
            "users": at("users", i),
            "sessions_running": at("sessions_running", i),
            "sessions_24h": at("sessions_24h", i),
        }
        for i, ts in enumerate(history.get("timestamps", []))
    ]
