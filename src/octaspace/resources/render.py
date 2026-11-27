from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any, cast

from .. import _normalize
from ..types import BatchResult, RenderBatchItem, RenderMachine, StartResult
from .base import Resource, pick, with_batch_ids


class RenderResource(Resource):
    """Render nodes: list and start (one or several)."""

    def list(self) -> list[RenderMachine]:
        """Return the nodes available for render (``GET /services/render``).

        Works without an API key, but is then refreshed about once an hour;
        with a key it is at most 10 seconds old.
        """
        data = self._request("GET", "/services/render", auth="optional")
        return cast("list[RenderMachine]", _normalize.machines(data))

    def start(self, node_number: str) -> StartResult:
        """Rent a node as a render node (``POST /services/render``).

        Billed by the hour until you stop the session. Never retried
        automatically.

        Raises:
            ServiceUnavailableError: Render is temporarily unavailable.
            ValidationError: The request was rejected, for example
                ``Insufficient balance``.
        """
        body = {"node_number": node_number}
        return cast(StartResult, self._request("POST", "/services/render", body=body))

    def start_batch(self, items: Sequence[RenderBatchItem]) -> builtins.list[BatchResult]:
        """Rent several render nodes at once (``POST /services/render``).

        Unlike ``start()``, a temporarily unavailable service is reported for
        each item (``status`` 1), not raised.

        Raises:
            TypeError: Two items have the same ``id``, or an item has an
                unknown field. Nothing is sent.
        """
        body = [
            pick(item, ("id", "node_number"), "render.start_batch()")
            for item in with_batch_ids(cast("Sequence[Mapping[str, Any]]", items))
        ]
        return cast(
            "builtins.list[BatchResult]", self._request("POST", "/services/render", body=body)
        )
