from __future__ import annotations

from typing import Any

from ...response import APIResponse
from ..base import Resource


class VpnResource(Resource):
    """VPN gateways for rent."""

    def list(self, **params: Any) -> APIResponse:
        """List the VPN gateways available for rent.

        ``GET /services/vpn``.
        """
        return self.get("/services/vpn", params=params or None)

    def create(self, **attrs: Any) -> APIResponse:
        """Start a VPN session.

        ``POST /services/vpn``. Never retried.

        Args:
            **attrs: The request body: ``node_id`` (required), ``subkind`` (the
                VPN protocol, ``"wg"`` by default) and ``protocol``.

        Returns:
            The response; ``data["uuid"]`` is the session UUID.
        """
        return self.post("/services/vpn", body=attrs)
