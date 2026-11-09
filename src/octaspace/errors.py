from __future__ import annotations

from typing import Any

from .response import APIResponse


class OctaSpaceError(Exception):
    """Base class for all SDK exceptions."""


class ConfigurationError(OctaSpaceError, ValueError):
    """Raised when the client is configured incorrectly."""


class NetworkError(OctaSpaceError):
    """Base class for transport-level failures."""


class APIConnectionError(NetworkError):
    """Raised when a network connection cannot be established."""


class APITimeoutError(NetworkError):
    """Raised when a request times out."""


class APIError(OctaSpaceError):
    """Raised for an error response from the API.

    Attributes:
        status_code: The HTTP status.
        request_id: The ``X-Request-Id`` header of the response, or ``None``.
        response: The full ``APIResponse``.
    """

    def __init__(self, message: str | None = None, *, response: APIResponse) -> None:
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.request_id
        super().__init__(message or _message_from_response(response))


class AuthenticationError(APIError):
    """Raised for HTTP 401 responses."""


class APIPermissionError(APIError):
    """Raised for HTTP 403 responses."""


class NotFoundError(APIError):
    """Raised for HTTP 404 responses."""


class ValidationError(APIError):
    """Raised for HTTP 400 and 422 responses: the request was rejected."""


class ConflictError(APIError):
    """Raised for HTTP 409 responses."""


class RateLimitError(APIError):
    """Raised for HTTP 429 responses.

    Attributes:
        retry_after: Seconds the API asks you to wait, or ``None``.
    """

    def __init__(self, message: str | None = None, *, response: APIResponse) -> None:
        self.retry_after = response.retry_after
        super().__init__(message, response=response)


class ServerError(APIError):
    """Raised for HTTP 5xx responses."""


class BadGatewayError(ServerError):
    """Raised for HTTP 502 responses."""


class ServiceUnavailableError(ServerError):
    """Raised for HTTP 503 responses."""


class GatewayTimeoutError(ServerError):
    """Raised for HTTP 504 responses."""


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


def _message_from_response(response: APIResponse) -> str:
    payload = response.data
    if isinstance(payload, dict):
        for key in ("error", "message", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return f"OctaSpace API error ({response.status_code})"


def from_response(response: APIResponse) -> APIError:
    """Return the error class instance that matches the response status."""
    error_type = STATUS_ERRORS.get(response.status_code)
    if error_type is None:
        error_type = ServerError if response.is_server_error else APIError
    return error_type(response=response)


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
