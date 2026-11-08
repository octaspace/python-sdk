from __future__ import annotations

from typing import Any

from ...response import APIResponse
from ..base import Resource


class RenderResource(Resource):
    """Render nodes for rent."""

    def list(self, **params: Any) -> APIResponse:
        """List the render nodes available for rent.

        ``GET /services/render``.
        """
        return self.get("/services/render", params=params or None)

    def create(self, **attrs: Any) -> APIResponse:
        """Start a render session.

        ``POST /services/render``. Retried only when the connection
        could not be established.

        Args:
            **attrs: The request body: ``node_id`` and ``disk_size`` (GB),
                optionally ``envs`` and ``multi-gpu-worker``.

        Returns:
            The response; ``data["uuid"]`` is the session UUID.
        """
        return self.post("/services/render", body=attrs)
