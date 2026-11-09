from __future__ import annotations

from typing import Any

from ..._transport.base import BaseTransport
from ...response import APIResponse
from ..base import Resource


class SessionProxy(Resource):
    """Operations of one session, returned by ``client.services.session(uuid)``."""

    def __init__(self, transport: BaseTransport, uuid: str) -> None:
        super().__init__(transport)
        self._uuid = self.encode(uuid)

    def info(self) -> APIResponse:
        """Return the session details.

        ``GET /services/{uuid}/info``. The fields depend on the kind of
        session, for example ``is_ready``, ``urls``, ``ssh_direct`` and
        ``vpn_config``.

        Raises:
            NotFoundError: The session does not exist.
        """
        return self.get(f"/services/{self._uuid}/info")

    def logs(self) -> APIResponse:
        """Return the session logs.

        ``GET /services/{uuid}/logs``. ``data["container"]`` is the container
        output, ``data["system"]`` the platform's events.
        """
        return self.get(f"/services/{self._uuid}/logs")

    def stop(self, **params: Any) -> APIResponse:
        """Stop the session.

        ``POST /services/{uuid}/stop``. Retried only when the connection could
        not be established.

        Args:
            **params: Optional ``score``, your integer rating of the session.
        """
        return self.post(
            f"/services/{self._uuid}/stop",
            body=params or None,
        )
