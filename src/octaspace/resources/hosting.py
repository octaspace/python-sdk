from __future__ import annotations

from typing import cast

from .. import _normalize
from ..types import HostingNode
from .base import Resource, segment


class HostingResource(Resource):
    """The nodes you host: state, prices and maintenance."""

    def nodes(self) -> list[HostingNode]:
        """Return your online nodes (``GET /hosting/nodes``).

        Each node has its status, the services it is offered for, prices,
        hardware, location and uptime. Offline nodes are not listed. A node
        that runs only VPN sessions stays ``idle``.
        """
        data = self._request("GET", "/hosting/nodes")
        return cast("list[HostingNode]", _normalize.null_strings(data))

    def get(self, number: str) -> HostingNode:
        """Return one of your online nodes (``GET /hosting/nodes/{number}``).

        Raises:
            NotFoundError: The node is offline, does not exist or is not yours.
            ValidationError: The node number is malformed.
        """
        data = self._request("GET", f"/hosting/nodes/{segment(number)}")
        return cast(HostingNode, _normalize.null_strings(data))

    def set_prices(
        self,
        number: str,
        *,
        base: int | None = None,
        storage: int | None = None,
        traffic: int | None = None,
        min_rent_minutes: int | None = None,
    ) -> None:
        """Change some prices of a node (``PATCH /hosting/nodes/{number}/prices``).

        Only the prices you pass change; at least one is required. Amounts are
        integer micro-USD (convert dollars with ``octaspace.usd_to_micro_usd()``).
        The listings show the new prices within a few seconds. Never retried
        automatically.

        Args:
            number: The node number.
            base: Charged for every hour the node is rented; $0.0001 to $1000.
            storage: Charged per hour for each GB of disk the renter
                allocates; $0 to $1000.
            traffic: Charged for each GB of network traffic; $0.0001 to $1000.
            min_rent_minutes: Minimum rent of a compute session, 0 to 60
                minutes; 0 turns it off.

        Raises:
            TypeError: No price is given, or one is not an integer.
            ValidationError: A price is out of range.
            NotFoundError: The node is not yours or does not exist.
        """
        prices = {
            "base": base,
            "storage": storage,
            "traffic": traffic,
            "min_rent_minutes": min_rent_minutes,
        }
        body = {key: value for key, value in prices.items() if value is not None}
        if not body:
            raise TypeError(
                "set_prices() needs at least one of base, storage, traffic, min_rent_minutes"
            )
        for key, value in body.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{key} must be an integer (micro-USD or minutes), got {value!r}")
        self._request("PATCH", f"/hosting/nodes/{segment(number)}/prices", body=body)

    def start_maintenance(self, number: str) -> None:
        """Put a node in maintenance (``PUT /hosting/nodes/{number}/maintenance``).

        The node is no longer offered for new rentals; running sessions go on
        and their renters are notified. Works for an offline node too.
        Calling it again changes nothing.

        Raises:
            NotFoundError: The node is not yours or does not exist.
            ValidationError: The node number is malformed.
        """
        self._request("PUT", f"/hosting/nodes/{segment(number)}/maintenance")

    def end_maintenance(self, number: str) -> None:
        """Offer a node for rent again (``DELETE /hosting/nodes/{number}/maintenance``).

        Calling it again changes nothing.

        Raises:
            NotFoundError: The node is not yours or does not exist.
            ValidationError: The node number is malformed.
        """
        self._request("DELETE", f"/hosting/nodes/{segment(number)}/maintenance")
