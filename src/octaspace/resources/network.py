from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class NetworkResource(Resource):
    """Statistics of the OctaSpace network."""

    def info(self) -> APIResponse:
        """Return network, blockchain and GPU market statistics.

        ``GET /network``. Works without an API token.
        """
        return self.get("/network")
