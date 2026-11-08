from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

import httpx

from .response import APIResponse


@dataclass(frozen=True, slots=True)
class RequestContext:
    """A request as passed to the ``on_request`` hook.

    Attributes:
        method: The HTTP method in lower case.
        path: The URL path.
        params: The query parameters.
    """

    method: str
    path: str
    params: dict[str, Any]

    @classmethod
    def from_httpx(cls, request: httpx.Request) -> RequestContext:
        """Build a ``RequestContext`` from an ``httpx.Request``."""
        params = dict(parse_qsl(request.url.query.decode("utf-8"), keep_blank_values=True))
        return cls(method=request.method.lower(), path=request.url.path, params=params)


RequestHook = Callable[[RequestContext], None]
ResponseHook = Callable[[APIResponse], None]


class HookDispatcher:
    """Runs the ``on_request`` / ``on_response`` hooks and the request log."""

    def __init__(
        self,
        on_request: RequestHook | None = None,
        on_response: ResponseHook | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._on_request = on_request
        self._on_response = on_response
        self._logger = logger

    def event_hooks(self) -> dict[str, list[Callable[[Any], None]]]:
        hooks: dict[str, list[Callable[[Any], None]]] = {}
        if self._on_request is not None or self._logger is not None:
            hooks["request"] = [self._handle_request]
        if self._on_response is not None:
            hooks["response"] = [self._handle_response]
        return hooks

    def response_wrapper(self, response: httpx.Response) -> APIResponse:
        wrapped = response.extensions.get("octaspace_api_response")
        if isinstance(wrapped, APIResponse):
            return wrapped
        wrapped = APIResponse.from_httpx(response)
        response.extensions["octaspace_api_response"] = wrapped
        if self._on_response is not None:
            self._on_response(wrapped)
        return wrapped

    def _handle_request(self, request: httpx.Request) -> None:
        context = RequestContext.from_httpx(request)
        if self._logger is not None:
            self._logger.debug("octaspace -> %s %s", request.method, request.url)
        if self._on_request is not None:
            self._on_request(context)

    def _handle_response(self, response: httpx.Response) -> None:
        # httpx response hooks run before the body is guaranteed to be buffered.
        # Read it here so APIResponse can safely cache bytes and parsed JSON once.
        response.read()
        wrapped = APIResponse.from_httpx(response)
        response.extensions["octaspace_api_response"] = wrapped
        if self._on_response is not None:
            self._on_response(wrapped)
