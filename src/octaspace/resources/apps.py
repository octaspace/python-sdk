from __future__ import annotations

from typing import Any

from ..response import APIResponse
from .base import Resource


class AppsResource(Resource):
    """Applications that can be started on rented machines."""

    def list(self, **params: Any) -> APIResponse:
        """List the applications.

        ``GET /apps``. Works without an API token.

        Args:
            **params: Query parameters sent as they are.
        """
        return self.get("/apps", params=params or None)
