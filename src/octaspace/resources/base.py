from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .._transport.base import BaseTransport
from ..response import APIResponse


class Resource:
    """Base class of the resources; sends requests through the client's transport."""

    def __init__(self, transport: BaseTransport) -> None:
        self._transport = transport

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self._transport.get(path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self._transport.post(path, body=body, headers=headers)

    def put(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self._transport.put(path, body=body, headers=headers)

    def patch(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self._transport.patch(path, body=body, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self._transport.delete(path, params=params, headers=headers)

    @staticmethod
    def encode(segment: str | int) -> str:
        return quote(str(segment), safe="")
