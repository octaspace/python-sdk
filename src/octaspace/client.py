from __future__ import annotations

from typing import Any

from ._transport.base import BaseTransport
from ._transport.httpx_transport import HttpxTransport
from .config import ClientConfig
from .errors import ConfigurationError
from .resources import (
    AccountsResource,
    AppsResource,
    IdleJobsResource,
    NetworkResource,
    NodesResource,
    ServicesResource,
    SessionsResource,
)


class OctaSpaceClient:
    """Client of the OctaSpace API.

    Args:
        api_key: The API token of your account (Account → Credentials →
            API Token). Without it, only the calls that need no token work.
        transport: A custom transport, for example
            ``octaspace._transport.mock_transport.MockTransport`` in tests.
        config: Base configuration; ``api_key`` and ``**overrides`` take
            precedence over it.
        **overrides: Any ``ClientConfig`` field, such as ``read_timeout``.

    Raises:
        ConfigurationError: An option is unknown or invalid.

    Use the client as a context manager, or call ``close()`` when done.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: BaseTransport | None = None,
        config: ClientConfig | None = None,
        **overrides: Any,
    ) -> None:
        self._config = self._build_config(api_key, config, overrides)
        self._transport = transport or HttpxTransport(self._config)
        self.accounts = AccountsResource(self._transport)
        self.nodes = NodesResource(self._transport)
        self.sessions = SessionsResource(self._transport)
        self.apps = AppsResource(self._transport)
        self.network = NetworkResource(self._transport)
        self.services = ServicesResource(self._transport)
        self.idle_jobs = IdleJobsResource(self._transport)

    @property
    def config(self) -> ClientConfig:
        """The configuration of this client."""
        return self._config

    def close(self) -> None:
        """Close the client's connections."""
        self._transport.close()

    def shutdown(self) -> None:
        """Close the client's connections; same as ``close()``."""
        self.close()

    def transport_stats(self) -> dict[str, Any]:
        """Return the connection mode, pool limits and API hosts in use."""
        return self._transport.transport_stats()

    def __enter__(self) -> OctaSpaceClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        del exc_type, exc, tb
        self.close()

    @staticmethod
    def _build_config(
        api_key: str | None,
        config: ClientConfig | None,
        overrides: dict[str, Any],
    ) -> ClientConfig:
        base = config.with_overrides() if config is not None else ClientConfig()
        try:
            if api_key is not None:
                base = base.with_overrides(api_key=api_key)
            return base.with_overrides(**overrides) if overrides else base
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
