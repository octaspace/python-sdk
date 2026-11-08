from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class APIResponse:
    """A response of the API.

    Attributes:
        status_code: The HTTP status.
        headers: The response headers.
        body: The raw body.
        data: The parsed JSON body, or ``None`` if the body is empty or not JSON.
        raw_response: The underlying ``httpx.Response``.
    """

    status_code: int
    headers: httpx.Headers
    body: bytes
    data: Any = None
    raw_response: httpx.Response | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_httpx(cls, response: httpx.Response) -> APIResponse:
        """Build an ``APIResponse`` from an ``httpx.Response``."""
        body = response.content
        data: Any = None
        content_type = response.headers.get("content-type", "")
        if body and "json" in content_type.lower():
            try:
                data = response.json()
            except ValueError:
                data = None
        return cls(
            status_code=response.status_code,
            headers=response.headers,
            body=body,
            data=data,
            raw_response=response,
        )

    @property
    def request_id(self) -> str | None:
        """The ``X-Request-Id`` header, or ``None``."""
        value = self.headers.get("x-request-id")
        return str(value) if value is not None else None

    @property
    def retry_after(self) -> int | None:
        """The ``Retry-After`` header in whole seconds, or ``None``.

        Accepts both forms of the header: a number of seconds or an HTTP date.
        """
        value = self.headers.get("retry-after")
        if value is None:
            return None
        if value.strip().isdigit():
            return int(value)
        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        return max(math.ceil((when - datetime.now(UTC)).total_seconds()), 0)

    @property
    def is_success(self) -> bool:
        """Whether the status is 2xx."""
        return 200 <= self.status_code <= 299

    @property
    def is_client_error(self) -> bool:
        """Whether the status is 4xx."""
        return 400 <= self.status_code <= 499

    @property
    def is_server_error(self) -> bool:
        """Whether the status is 5xx."""
        return 500 <= self.status_code <= 599

    @property
    def is_error(self) -> bool:
        """Whether the status is 4xx or 5xx."""
        return self.is_client_error or self.is_server_error

    def raise_for_status(self) -> None:
        """Raise the matching ``APIError`` if the status is 4xx or 5xx."""
        if self.is_error:
            from .errors import raise_for_response

            raise_for_response(self)

    def __str__(self) -> str:
        return f"<APIResponse [{self.status_code}]>"
