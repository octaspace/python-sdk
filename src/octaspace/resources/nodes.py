from __future__ import annotations

from typing import Any

from ..response import APIResponse
from .base import Resource


class NodesResource(Resource):
    """The nodes you host."""

    def list(self, **params: Any) -> APIResponse:
        """List your nodes.

        ``GET /nodes``.

        Args:
            **params: Query parameters sent as they are.
        """
        return self.get("/nodes", params=params or None)

    def find(self, node_id: int | str) -> APIResponse:
        """Return one of your nodes.

        ``GET /nodes/{node_id}``.

        Raises:
            NotFoundError: The node does not exist or is not yours.
        """
        return self.get(f"/nodes/{self.encode(node_id)}")

    def download_ident(self, node_id: int | str) -> APIResponse:
        """Download the identity file of a node.

        ``GET /nodes/{node_id}/ident``. Read the file from ``.body``.
        """
        return self.get(f"/nodes/{self.encode(node_id)}/ident")

    def download_logs(self, node_id: int | str) -> APIResponse:
        """Download the logs of a node.

        ``GET /nodes/{node_id}/logs``. Read the logs from ``.body``.
        """
        return self.get(f"/nodes/{self.encode(node_id)}/logs")

    def update_prices(self, node_id: int | str, **prices: Any) -> APIResponse:
        """Set the prices of a node.

        ``PATCH /nodes/{node_id}/prices``. Never retried.

        Args:
            node_id: Your node.
            **prices: One or more of ``base``, ``storage`` and ``traffic``, each
                an integer from 0 to 10000.

        Raises:
            APIError: Status 400 for an unknown field or a value out of range.
        """
        return self.patch(f"/nodes/{self.encode(node_id)}/prices", body=prices)

    def reboot(self, node_id: int | str) -> APIResponse:
        """Reboot a node.

        ``GET /nodes/{node_id}/reboot``. Retried like any GET request.
        """
        return self.get(f"/nodes/{self.encode(node_id)}/reboot")
