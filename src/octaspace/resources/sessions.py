from __future__ import annotations

from typing import Any

from ..response import APIResponse
from .base import Resource


class SessionsResource(Resource):
    """Your sessions of every kind."""

    def list(self, **params: Any) -> APIResponse:
        """List your sessions.

        ``GET /sessions``.

        Args:
            **params: Query parameters; ``recent=True`` returns recent sessions
                instead of the active ones.
        """
        return self.get("/sessions", params=params or None)
