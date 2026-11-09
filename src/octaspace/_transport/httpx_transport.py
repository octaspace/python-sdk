from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import ClientConfig
from ..errors import APIConnectionError, APITimeoutError, NetworkError, raise_for_response
from ..hooks import HookDispatcher
from ..response import APIResponse
from .retry import can_resend, compute_backoff, is_retryable_response
from .rotator import UrlRotator


class HttpxTransport:
    def __init__(self, config: ClientConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._hooks = HookDispatcher(config.on_request, config.on_response, config.logger)
        self._rotator = UrlRotator(config.urls) if len(config.urls) > 1 else None
        self._client = client or httpx.Client(
            timeout=config.build_timeout(),
            limits=config.build_limits(),
            verify=config.ssl_verify,
            event_hooks=self._hooks.event_hooks(),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        method = method.upper()
        path = path if path.startswith("/") else f"/{path}"
        attempt = 0
        while True:
            try:
                response = self._send_with_failover(
                    method, path, params=params, body=body, headers=headers
                )
            except httpx.TransportError as exc:
                if attempt >= self._config.max_retries or not can_resend(method, exc):
                    raise _network_error(exc) from exc
                time.sleep(self._backoff(attempt))
            else:
                delay = self._retry_delay(method, response, attempt)
                if delay is None:
                    if response.is_error:
                        raise_for_response(response)
                    return response
                time.sleep(delay)
            attempt += 1

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("POST", path, body=body, headers=headers)

    def put(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PUT", path, body=body, headers=headers)

    def patch(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PATCH", path, body=body, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("DELETE", path, params=params, headers=headers)

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

    def _retry_delay(self, method: str, response: APIResponse, attempt: int) -> float | None:
        """Seconds to wait before repeating the request, or ``None`` not to repeat it."""
        if attempt >= self._config.max_retries:
            return None
        if not is_retryable_response(method, response.status_code):
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
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        """Send to the next healthy host; move on to another one only when that is safe."""
        *fallbacks, last = self._ordered_urls()
        for base_url in fallbacks:
            try:
                return self._send_to_url(
                    base_url, method, path, params=params, body=body, headers=headers
                )
            except httpx.TransportError as exc:
                if not can_resend(method, exc):
                    raise
        return self._send_to_url(last, method, path, params=params, body=body, headers=headers)

    def _send_to_url(
        self,
        base_url: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        try:
            response = self._client.request(
                method,
                self._build_url(base_url, path),
                params=params,
                json=body,
                headers=self._default_headers(headers),
            )
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

    def _default_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        merged = {
            "Accept": "application/json",
            "User-Agent": self._config.resolved_user_agent,
        }
        if self._config.api_key:
            merged["Authorization"] = self._config.api_key
        if not self._config.keep_alive:
            merged["Connection"] = "close"
        if headers:
            merged.update(headers)
        return merged

    @staticmethod
    def _build_url(base_url: str, path: str) -> str:
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _network_error(error: httpx.TransportError) -> NetworkError:
    if isinstance(error, httpx.TimeoutException):
        return APITimeoutError(str(error))
    return APIConnectionError(str(error))
