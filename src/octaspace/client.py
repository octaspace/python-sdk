from __future__ import annotations

from typing import Any

from ._transport.base import BaseTransport
from ._transport.httpx_transport import HttpxTransport
from .config import ClientConfig
from .resources import (
    AccountsResource,
    ComputeResource,
    HostingResource,
    NetworkResource,
    RenderResource,
    SessionsResource,
    StatsResource,
    VpnResource,
)
from .response import RateLimit


class OctaSpaceClient:
    """Client of the OctaSpace API.

    Args:
        api_key: An API key of your OctaSpace account (``octa_ak_…``), created
            in the dashboard under Account → Credentials → API Keys. Sent as
            ``Authorization: Bearer <key>``. Without it, only the calls that
            need no key work.
        transport: A custom transport, for tests.
        config: Base configuration; ``api_key`` and ``**overrides`` take
            precedence over it.
        **overrides: Any ``ClientConfig`` field, such as ``read_timeout``.

    Raises:
        ConfigurationError: An option is unknown or invalid.

    Attributes:
        accounts: Balance.
        compute: Machines and apps: list, apps, start, start_batch, restart.
        render: Render nodes: list, start, start_batch.
        vpn: VPN nodes: list, start.
        sessions: Running sessions: list, get, logs, stop, wait_ready, wait_stopped.
        hosting: Your nodes: nodes, get, set_prices, start_maintenance, end_maintenance.
        network: Platform statistics: info, history.
        stats: GPU market and mining: gpu_current, gpu_history, gpu_locations, mining.

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
        self._transport = transport if transport is not None else HttpxTransport(self._config)
        self.accounts = AccountsResource(self._transport)
        self.compute = ComputeResource(self._transport)
        self.render = RenderResource(self._transport)
        self.vpn = VpnResource(self._transport)
        self.sessions = SessionsResource(self._transport)
        self.hosting = HostingResource(self._transport)
        self.network = NetworkResource(self._transport)
        self.stats = StatsResource(self._transport)

    @property
    def config(self) -> ClientConfig:
        """The configuration of this client."""
        return self._config

    @property
    def rate_limit(self) -> RateLimit | None:
        """The rate limit state of the latest response that carried it, or ``None``."""
        return self._transport.rate_limit

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
        base = config if config is not None else ClientConfig()
        if api_key is not None:
            overrides = {**overrides, "api_key": api_key}
        return base.with_overrides(**overrides)
