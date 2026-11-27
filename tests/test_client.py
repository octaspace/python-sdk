from __future__ import annotations

import pytest

import octaspace
from octaspace import DEFAULT_BASE_URL, ClientConfig, ConfigurationError, OctaSpaceClient
from octaspace.resources import (
    AccountsResource,
    ComputeResource,
    HostingResource,
    NetworkResource,
    RenderResource,
    SessionsResource,
    StatsResource,
    VpnResource,
)


def test_client_has_every_resource() -> None:
    with OctaSpaceClient() as client:
        assert isinstance(client.accounts, AccountsResource)
        assert isinstance(client.compute, ComputeResource)
        assert isinstance(client.render, RenderResource)
        assert isinstance(client.vpn, VpnResource)
        assert isinstance(client.sessions, SessionsResource)
        assert isinstance(client.hosting, HostingResource)
        assert isinstance(client.network, NetworkResource)
        assert isinstance(client.stats, StatsResource)
        assert client.config.base_url == DEFAULT_BASE_URL == "https://api.octa.space"
        assert client.rate_limit is None


def test_shared_client_helpers() -> None:
    octaspace.configure(api_key="octa_ak_test")

    shared = octaspace.client()
    one_off = octaspace.client(api_key="octa_ak_other")

    assert shared is octaspace.client()
    assert one_off is not shared
    one_off.close()
    octaspace.shutdown_shared_client()


def test_client_rejects_unknown_override() -> None:
    with pytest.raises(ConfigurationError):
        OctaSpaceClient(unknown_option=True)


def test_client_does_not_mutate_passed_config() -> None:
    config = ClientConfig(api_key="octa_ak_config")
    with OctaSpaceClient(api_key="octa_ak_override", config=config) as client:
        assert config.api_key == "octa_ak_config"
        assert client.config.api_key == "octa_ak_override"


def test_api_url_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTA_API_URL", "https://a.example.com, https://b.example.com")
    monkeypatch.setenv("OCTA_BASE_URL", "https://ignored.example.com")

    config = ClientConfig.from_env()

    assert config.urls == ["https://a.example.com", "https://b.example.com"]


def test_base_url_environment_variable_still_works(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCTA_API_URL", raising=False)
    monkeypatch.setenv("OCTA_BASE_URL", "https://a.example.com")

    assert ClientConfig.from_env().urls == ["https://a.example.com"]
