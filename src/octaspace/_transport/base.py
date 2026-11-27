from __future__ import annotations

from typing import Any, Literal, Protocol

from ..response import APIResponse, RateLimit

AuthMode = Literal["required", "optional", "none"]
"""How a request authenticates.

- ``required``: sends the API key; raises ``AuthenticationError`` before sending without one.
- ``optional``: sends the API key when the client has one.
- ``none``: never sends the API key.
"""


class BaseTransport(Protocol):
    """Sends requests to the API; the client's resources use it."""

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        auth: AuthMode = "required",
        idempotent: bool = False,
    ) -> APIResponse: ...

    @property
    def rate_limit(self) -> RateLimit | None: ...

    def close(self) -> None: ...

    def transport_stats(self) -> dict[str, Any]: ...
