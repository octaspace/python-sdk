from __future__ import annotations

import re
import time
from typing import Any

import httpx

from ..config import ClientConfig
from ..errors import (
    API_KEY_PREFIX,
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    NetworkError,
    from_response,
)
from ..hooks import HookDispatcher
from ..response import APIResponse, RateLimit
from .base import AuthMode
from .retry import can_resend, compute_backoff, is_retryable_response
from .rotator import UrlRotator

_BEARER = re.compile(r"^bearer\s+", re.IGNORECASE)
_DASHBOARD_HINT = "the OctaSpace dashboard: Account → Credentials → API Keys"

APP_HEADER = "X-OCTA-APP"
"""Header that tells the API which app is calling; sent with every request."""
APP_NAME = "python-sdk"


def normalize_api_key(key: str | None) -> str | None:
    """Strip whitespace and a leading ``Bearer `` from a key; ``None`` for an empty one."""
    if key is None:
        return None
    key = _BEARER.sub("", key.strip())
    return key or None


class HttpxTransport:
    """Sends requests with ``httpx``: authentication, retries, failover and errors."""

    def __init__(self, config: ClientConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._api_key = normalize_api_key(config.api_key)
        self._hooks = HookDispatcher(config.on_request, config.on_response, config.logger)
        self._rotator = UrlRotator(config.urls) if len(config.urls) > 1 else None
        self._rate_limit: RateLimit | None = None
        self._client = client or httpx.Client(
            timeout=config.build_timeout(),
            limits=config.build_limits(),
            verify=config.ssl_verify,
            event_hooks=self._hooks.event_hooks(),
        )

    @property
    def rate_limit(self) -> RateLimit | None:
        """The rate limit state of the latest response that carried it."""
        return self._rate_limit

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        auth: AuthMode = "required",
        idempotent: bool = False,
    ) -> APIResponse:
        method = method.upper()
        path = path if path.startswith("/") else f"/{path}"
        headers = self._headers(method, path, auth, body)
        params = {key: value for key, value in (params or {}).items() if value is not None}
        attempt = 0
        while True:
            try:
                response = self._send_with_failover(
                    method,
                    path,
                    params=params or None,
                    body=body,
                    headers=headers,
                    idempotent=idempotent,
                )
            except httpx.TransportError as exc:
                if attempt >= self._config.max_retries or not can_resend(method, exc, idempotent):
                    raise _network_error(exc) from exc
                time.sleep(self._backoff(attempt))
            else:
                rate_limit = response.rate_limit
                if rate_limit is not None:
                    self._rate_limit = rate_limit
                delay = self._retry_delay(method, response, attempt, idempotent)
                if delay is None:
                    if response.is_error:
                        raise self._error(response)
                    _check_json(response)
                    return response
                time.sleep(delay)
            attempt += 1

    def close(self) -> None:
        self._client.close()

    def transport_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "mode": "persistent" if self._config.keep_alive else "standard",
            "limits": {
                "max_keepalive_connections": self._config.pool_size
                if self._config.keep_alive
                else 0,
                "max_connections": self._config.max_connections,
                "keepalive_expiry": (
                    self._config.idle_timeout if self._config.keep_alive else None
                ),
            },
        }
        if self._rotator is not None:
            stats["rotator"] = self._rotator.stats()
        else:
            stats["url"] = self._config.urls[0]
        return stats

    def _headers(self, method: str, path: str, auth: AuthMode, body: Any) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self._config.resolved_user_agent,
            APP_HEADER: APP_NAME,
        }
        if auth != "none":
            if self._api_key is not None:
                headers["Authorization"] = f"Bearer {self._api_key}"
            elif auth == "required":
                raise AuthenticationError(
                    f"An API key is required for {method} {path}: pass an API key "
                    f"({API_KEY_PREFIX}…) from {_DASHBOARD_HINT}",
                    response=APIResponse(status_code=401, headers=httpx.Headers(), body=b""),
                )
        if body is not None:
            headers["Content-Type"] = "application/json"
        if not self._config.keep_alive:
            headers["Connection"] = "close"
        return headers

    def _error(self, response: APIResponse) -> APIError:
        error = from_response(response)
        if (
            response.status_code == 401
            and self._api_key is not None
            and not self._api_key.startswith(API_KEY_PREFIX)
        ):
            return from_response(
                response,
                f'{error.message} (API keys start with "{API_KEY_PREFIX}"; create one in '
                f"{_DASHBOARD_HINT})",
            )
        return error

    def _retry_delay(
        self, method: str, response: APIResponse, attempt: int, idempotent: bool
    ) -> float | None:
        """Seconds to wait before repeating the request, or ``None`` not to repeat it."""
        if attempt >= self._config.max_retries:
            return None
        if not is_retryable_response(method, response.status_code, idempotent):
            return None
        retry_after = response.retry_after
        if retry_after is not None and retry_after > self._config.max_retry_after:
            return None
        return self._backoff(attempt, retry_after=retry_after)

    def _backoff(self, attempt: int, *, retry_after: int | None = None) -> float:
        return compute_backoff(
            attempt=attempt,
            retry_interval=self._config.retry_interval,
            backoff_factor=self._config.backoff_factor,
            retry_after=retry_after,
        )

    def _send_with_failover(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        body: Any,
        headers: dict[str, str],
        idempotent: bool,
    ) -> APIResponse:
        """Send to the next healthy host; move on to another one only when that is safe."""
        *fallbacks, last = self._ordered_urls()
        for base_url in fallbacks:
            try:
                return self._send_to_url(base_url, method, path, params, body, headers)
            except httpx.TransportError as exc:
                if not can_resend(method, exc, idempotent):
                    raise
        return self._send_to_url(last, method, path, params, body, headers)

    def _send_to_url(
        self,
        base_url: str,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        body: Any,
        headers: dict[str, str],
    ) -> APIResponse:
        try:
            response = self._client.request(
                method,
                f"{base_url.rstrip('/')}{path}",
                params=params,
                json=body,
                headers=headers,
            )
            response.read()
        except httpx.TransportError:
            if self._rotator is not None:
                self._rotator.mark_failed(base_url)
            raise
        if self._rotator is not None:
            self._rotator.mark_success(base_url)
        return self._hooks.response_wrapper(response)

    def _ordered_urls(self) -> list[str]:
        if self._rotator is None:
            return [self._config.urls[0]]
        primary = self._rotator.next_url()
        available = self._rotator.available_urls()
        remainder = [url for url in available if url != primary]
        return [primary, *remainder]


def _check_json(response: APIResponse) -> None:
    """Raise when a successful response has a body that is not JSON, e.g. a proxy's HTML page."""
    if response.body.strip() and response.data is None:
        raise APIError(
            f"Response is not valid JSON (status {response.status_code})", response=response
        )


def _network_error(error: httpx.TransportError) -> NetworkError:
    if isinstance(error, httpx.TimeoutException):
        return APITimeoutError(str(error) or "Request timed out")
    return APIConnectionError(str(error) or "Connection failed")
