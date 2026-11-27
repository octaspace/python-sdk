from __future__ import annotations

from typing import cast

from .. import _normalize
from ..types import StartResult, VpnMachine, VpnProtocol
from .base import Resource


class VpnResource(Resource):
    """VPN nodes: list and start."""

    def list(self) -> list[VpnMachine]:
        """Return the nodes offered for VPN (``GET /services/vpn``).

        Works without an API key, but is then refreshed about once an hour;
        with a key it is at most 10 seconds old.
        """
        data = self._request("GET", "/services/vpn", auth="optional")
        return cast("list[VpnMachine]", _normalize.null_strings(data))

    def start(self, node_number: str, subkind: VpnProtocol) -> StartResult:
        """Start a VPN session (``POST /services/vpn``), billed by traffic until stopped.

        Pick ``subkind`` from the node's ``protocols``. Once
        ``sessions.wait_ready()`` returns the session, its ``config`` is what
        the client connects with. You can have one VPN session per node.
        Never retried automatically.

        Args:
            node_number: The node, from ``list()``.
            subkind: ``wg`` (WireGuard), ``awg`` (AmneziaWG), ``reality``
                (VLESS Reality) or ``http_proxy`` (an HTTP proxy with a login).

        Raises:
            ValidationError: The request was rejected, for example
                ``Insufficient balance``, ``Node not found``, ``You already
                have a VPN session on this node``, or ``Node's VPN did not pass
                the connection check`` for a protocol the node did not pass.
        """
        body = {"node_number": node_number, "subkind": subkind}
        return cast(StartResult, self._request("POST", "/services/vpn", body=body))
