from __future__ import annotations

from typing import Any

from .response import APIResponse, RateLimit

API_KEY_PREFIX = "octa_ak_"
"""Prefix of OctaSpace API keys."""

_MAX_MESSAGE_LENGTH = 512


class OctaSpaceError(Exception):
    """Base class for all SDK exceptions."""


class ConfigurationError(OctaSpaceError, ValueError):
    """Raised when the client is configured incorrectly."""


class NetworkError(OctaSpaceError):
    """Base class for failures to reach the API."""


class APIConnectionError(NetworkError):
    """Raised when the API cannot be reached: DNS, connection or TLS failure."""


class APITimeoutError(NetworkError):
    """Raised when a request takes longer than its timeout."""


class WaitTimeoutError(OctaSpaceError, TimeoutError):
    """Raised by ``sessions.wait_ready()`` and ``wait_stopped()`` after their ``timeout``."""


class APIError(OctaSpaceError):
    """Raised for an error response from the API.

    Attributes:
        status_code: The HTTP status.
        message: The API's message, for example ``Insufficient balance``.
        code: A machine-readable code from the body, or ``None``.
        body: The parsed JSON body, or ``None``.
        request_id: The ``X-Request-Id`` header, or ``None``. Include it when
            you contact support.
        retry_after: Seconds the API asks you to wait (``Retry-After``), or ``None``.
        rate_limit: The rate limit state of this response, or ``None``.
        response: The full ``APIResponse``.
    """

    def __init__(self, message: str | None = None, *, response: APIResponse) -> None:
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.request_id
        self.retry_after = response.retry_after
        self.rate_limit: RateLimit | None = response.rate_limit
        self.body: Any = response.data
        code = response.data.get("code") if isinstance(response.data, dict) else None
        self.code: str | None = code if isinstance(code, str) else None
        self.message = _truncate(message or _message_from_response(response))
        super().__init__(self.message)


class AuthenticationError(APIError):
    """HTTP 401: the API key is missing, wrong or deleted."""


class APIPermissionError(APIError):
    """HTTP 403: access denied."""


class NotFoundError(APIError):
    """HTTP 404: the resource does not exist.

    For a session this also means that it has stopped.
    """


class SessionStoppedError(NotFoundError):
    """Raised by ``sessions.wait_ready()`` when the session stops while it is starting."""


class ValidationError(APIError):
    """HTTP 400 or 422: the request was rejected; the message says why."""


class ConflictError(APIError):
    """HTTP 409: the session is already starting or restarting."""


class RateLimitError(APIError):
    """HTTP 429: too many requests. Wait ``retry_after`` seconds."""


class ServerError(APIError):
    """HTTP 5xx: a temporary problem on the API side."""


class BadGatewayError(ServerError):
    """HTTP 502."""


class ServiceUnavailableError(ServerError):
    """HTTP 503: the service is temporarily unavailable; retry later."""


class GatewayTimeoutError(ServerError):
    """HTTP 504."""


STATUS_ERRORS: dict[int, type[APIError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: APIPermissionError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}


def _truncate(message: str) -> str:
    if len(message) > _MAX_MESSAGE_LENGTH:
        return message[:_MAX_MESSAGE_LENGTH] + "…"
    return message


def _message_from_response(response: APIResponse) -> str:
    payload = response.data
    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    text = response.body.decode("utf-8", errors="replace").strip()
    if text and payload is None:
        return text
    return f"Request failed with status {response.status_code}"


def from_response(response: APIResponse, message: str | None = None) -> APIError:
    """Return the error class instance that matches the response status."""
    error_type = STATUS_ERRORS.get(response.status_code)
    if error_type is None:
        error_type = ServerError if response.is_server_error else APIError
    return error_type(message, response=response)


def raise_for_response(response: APIResponse) -> None:
    """Raise the error that matches the response status."""
    raise from_response(response)


def error_context(error: Exception) -> dict[str, Any]:
    """Return the status, request ID and message of an error as a dict."""
    if isinstance(error, APIError):
        return {
            "status_code": error.status_code,
            "request_id": error.request_id,
            "message": str(error),
        }
    return {"message": str(error)}
