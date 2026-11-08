from __future__ import annotations

import logging
import os
from dataclasses import dataclass, replace
from typing import Any

import httpx

from .__about__ import __version__
from .hooks import RequestHook, ResponseHook


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class ClientConfig:
    """Settings of an ``OctaSpaceClient``.

    Every field can be passed to ``OctaSpaceClient`` as a keyword argument.
    Timeouts and intervals are in seconds. See the client configuration guide
    for the meaning and default of each field.

    Raises:
        ValueError: A field has an invalid value.
    """

    api_key: str | None = None
    base_url: str = "https://api.octa.space"
    base_urls: list[str] | None = None
    keep_alive: bool = False
    pool_size: int = 5
    max_connections: int = 20
    pool_timeout: float = 5.0
    idle_timeout: float = 60.0
    open_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    max_retries: int = 2
    retry_interval: float = 0.5
    backoff_factor: float = 2.0
    ssl_verify: bool = True
    on_request: RequestHook | None = None
    on_response: ResponseHook | None = None
    logger: logging.Logger | None = None
    user_agent: str | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.strip()
        if not self.base_url:
            raise ValueError("base_url must be a non-empty string")

        if self.base_urls is not None:
            cleaned_urls = [str(url).strip() for url in self.base_urls if str(url).strip()]
            if not cleaned_urls:
                raise ValueError("base_urls must contain at least one non-empty URL")
            self.base_urls = cleaned_urls

        _validate_non_negative_int("pool_size", self.pool_size)
        _validate_positive_int("max_connections", self.max_connections)
        _validate_positive_float("pool_timeout", self.pool_timeout)
        _validate_positive_float("idle_timeout", self.idle_timeout)
        _validate_positive_float("open_timeout", self.open_timeout)
        _validate_positive_float("read_timeout", self.read_timeout)
        _validate_positive_float("write_timeout", self.write_timeout)
        _validate_non_negative_int("max_retries", self.max_retries)
        _validate_non_negative_float("retry_interval", self.retry_interval)
        _validate_positive_float("backoff_factor", self.backoff_factor)

    @property
    def urls(self) -> list[str]:
        """The API hosts in use: ``base_urls`` if set, otherwise ``[base_url]``."""
        return list(self.base_urls) if self.base_urls is not None else [self.base_url]

    @property
    def resolved_user_agent(self) -> str:
        """The ``User-Agent`` header the client sends."""
        if self.user_agent:
            return self.user_agent
        return f"octaspace-python/{__version__}"

    def build_timeout(self) -> httpx.Timeout:
        """Return the timeouts as an ``httpx.Timeout``."""
        return httpx.Timeout(
            connect=self.open_timeout,
            read=self.read_timeout,
            write=self.write_timeout,
            pool=self.pool_timeout,
        )

    def build_limits(self) -> httpx.Limits:
        """Return the connection pool limits as an ``httpx.Limits``."""
        keepalive_connections = self.pool_size if self.keep_alive else 0
        keepalive_expiry = self.idle_timeout if self.keep_alive else None
        return httpx.Limits(
            max_keepalive_connections=keepalive_connections,
            max_connections=self.max_connections,
            keepalive_expiry=keepalive_expiry,
        )

    def with_overrides(self, **overrides: Any) -> ClientConfig:
        """Return a copy with the given fields replaced.

        Raises:
            ValueError: A field is unknown or invalid.
        """
        try:
            return replace(self, **overrides)
        except TypeError as exc:
            raise ValueError(str(exc)) from exc

    @classmethod
    def from_env(cls, **overrides: Any) -> ClientConfig:
        """Build a configuration from ``OCTA_*`` environment variables.

        Reads ``OCTA_API_KEY``, ``OCTA_BASE_URL``, ``OCTA_BASE_URLS``
        (comma-separated) and one variable per option, for example
        ``OCTA_READ_TIMEOUT``. ``OCTA_LOGGER`` is the name of a logger.

        Args:
            **overrides: Fields that take precedence over the environment.
        """
        defaults = cls()
        base_urls = os.getenv("OCTA_BASE_URLS")
        logger_name = os.getenv("OCTA_LOGGER")
        logger = logging.getLogger(logger_name) if logger_name else None
        config = cls(
            api_key=os.getenv("OCTA_API_KEY"),
            base_url=os.getenv("OCTA_BASE_URL", defaults.base_url),
            base_urls=[item.strip() for item in base_urls.split(",")] if base_urls else None,
            keep_alive=_env_bool(os.getenv("OCTA_KEEP_ALIVE"), defaults.keep_alive),
            pool_size=int(os.getenv("OCTA_POOL_SIZE", defaults.pool_size)),
            max_connections=int(os.getenv("OCTA_MAX_CONNECTIONS", defaults.max_connections)),
            pool_timeout=float(os.getenv("OCTA_POOL_TIMEOUT", defaults.pool_timeout)),
            idle_timeout=float(os.getenv("OCTA_IDLE_TIMEOUT", defaults.idle_timeout)),
            open_timeout=float(os.getenv("OCTA_OPEN_TIMEOUT", defaults.open_timeout)),
            read_timeout=float(os.getenv("OCTA_READ_TIMEOUT", defaults.read_timeout)),
            write_timeout=float(os.getenv("OCTA_WRITE_TIMEOUT", defaults.write_timeout)),
            max_retries=int(os.getenv("OCTA_MAX_RETRIES", defaults.max_retries)),
            retry_interval=float(os.getenv("OCTA_RETRY_INTERVAL", defaults.retry_interval)),
            backoff_factor=float(os.getenv("OCTA_BACKOFF_FACTOR", defaults.backoff_factor)),
            ssl_verify=_env_bool(os.getenv("OCTA_SSL_VERIFY"), defaults.ssl_verify),
            logger=logger,
            user_agent=os.getenv("OCTA_USER_AGENT"),
        )
        return config.with_overrides(**overrides) if overrides else config


def _validate_non_negative_int(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0")


def _validate_positive_int(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0")


def _validate_non_negative_float(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0")


def _validate_positive_float(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
