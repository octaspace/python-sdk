from __future__ import annotations

from typing import Any

from .__about__ import __version__
from .client import OctaSpaceClient
from .config import ClientConfig
from .errors import (
    APIConnectionError,
    APIError,
    APIPermissionError,
    APITimeoutError,
    AuthenticationError,
    BadGatewayError,
    ConfigurationError,
    GatewayTimeoutError,
    NetworkError,
    NotFoundError,
    OctaSpaceError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    ValidationError,
)

_configuration = ClientConfig()
_shared_client: OctaSpaceClient | None = None


def configuration() -> ClientConfig:
    """Return the global configuration."""
    return _configuration


def configure(**overrides: Any) -> ClientConfig:
    """Update the global configuration and close the shared client.

    Args:
        **overrides: Any ``ClientConfig`` field.

    Returns:
        The new global configuration.
    """
    global _configuration, _shared_client
    _configuration = _configuration.with_overrides(**overrides)
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None
    return _configuration


def reset_configuration() -> ClientConfig:
    """Close the shared client and restore the default configuration."""
    global _configuration, _shared_client
    if _shared_client is not None:
        _shared_client.close()
    _shared_client = None
    _configuration = ClientConfig()
    return _configuration


def client(api_key: str | None = None, **overrides: Any) -> OctaSpaceClient:
    """Return the shared client, or a new client when arguments are given.

    Without arguments, returns one client built from the global configuration
    and reused on every call. With ``api_key`` or other options, returns a new
    client based on the global configuration; close it yourself.
    """
    global _shared_client
    if api_key is None and not overrides:
        if _shared_client is None:
            _shared_client = OctaSpaceClient(config=_configuration)
        return _shared_client
    local_config = _configuration.with_overrides(**overrides) if overrides else _configuration
    return OctaSpaceClient(api_key=api_key, config=local_config)


def shutdown_shared_client() -> None:
    """Close the shared client; the next ``client()`` call creates a new one."""
    global _shared_client
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None


__all__ = [
    "APIConnectionError",
    "APIError",
    "APIPermissionError",
    "APITimeoutError",
    "AuthenticationError",
    "BadGatewayError",
    "ClientConfig",
    "ConfigurationError",
    "GatewayTimeoutError",
    "NetworkError",
    "NotFoundError",
    "OctaSpaceClient",
    "OctaSpaceError",
    "RateLimitError",
    "ServerError",
    "ServiceUnavailableError",
    "ValidationError",
    "__version__",
    "client",
    "configuration",
    "configure",
    "reset_configuration",
    "shutdown_shared_client",
]
