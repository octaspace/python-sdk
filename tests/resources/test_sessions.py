from __future__ import annotations

import httpx
import pytest

from helpers import API, load_fixture
from octaspace import (
    NotFoundError,
    SessionStoppedError,
    WaitTimeoutError,
    is_compute_session,
    is_render_session,
    is_vpn_session,
)

UUID = "96e33710-ec12-11ed-8588-fa163e49e8aa"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []
    monkeypatch.setattr("octaspace.resources.sessions.time.sleep", calls.append)
    return calls


def test_list_and_get(respx_mock, client) -> None:
    ready = load_fixture("session_compute_ready.json")
    respx_mock.get(f"{API}/sessions").respond(json=[ready, load_fixture("session_vpn_ready.json")])
    respx_mock.get(f"{API}/services/{UUID}/info").respond(json=ready)

    sessions = client.sessions.list()
    session = client.sessions.get(UUID)

    assert is_compute_session(sessions[0]) and is_vpn_session(sessions[1])
    assert not is_render_session(sessions[0])
    assert session["status"] == "ready"


def test_sessions_need_a_key(anonymous) -> None:
    from octaspace import AuthenticationError

    with pytest.raises(AuthenticationError):
        anonymous.sessions.list()


def test_envs_keep_null_strings(respx_mock, client) -> None:
    session = load_fixture("session_compute_ready.json")
    session["envs"] = {"MODE": "null"}
    respx_mock.get(f"{API}/services/{UUID}/info").respond(json=session)

    result = client.sessions.get(UUID)

    assert is_compute_session(result)
    assert result.get("envs") == {"MODE": "null"}


def test_http_proxy_config(respx_mock, client) -> None:
    respx_mock.get(f"{API}/services/{UUID}/info").respond(
        json=load_fixture("session_vpn_http_proxy.json")
    )

    session = client.sessions.get(UUID)

    assert is_vpn_session(session)
    config = session.get("config")
    assert isinstance(config, dict) and config["port"] == 40000


def test_logs(respx_mock, client) -> None:
    route = respx_mock.get(f"{API}/services/{UUID}/logs").respond(
        json=load_fixture("session_logs.json")
    )

    logs = client.sessions.logs(UUID, tail=50)

    assert route.calls.last.request.url.params["tail"] == "50"
    assert isinstance(logs["system"], list)


def test_stop_is_retried(respx_mock) -> None:
    from octaspace import OctaSpaceClient

    route = respx_mock.post(f"{API}/services/{UUID}/stop")
    route.side_effect = [httpx.Response(503, json={}), httpx.Response(202)]
    with OctaSpaceClient(api_key="octa_ak_test", max_retries=1, retry_interval=0) as client:
        assert client.sessions.stop(UUID) == {"uuid": UUID}
    assert route.call_count == 2


def test_wait_ready(respx_mock, client, no_sleep) -> None:
    route = respx_mock.get(f"{API}/services/{UUID}/info")
    route.side_effect = [
        httpx.Response(200, json=load_fixture("session_compute_starting.json")),
        httpx.Response(200, json=load_fixture("session_compute_ready.json")),
    ]
    seen: list[str] = []

    session = client.sessions.wait_ready(
        UUID, interval=2, on_progress=lambda s: seen.append(s["status"])
    )

    assert session["status"] == "ready"
    assert seen == ["starting", "ready"]
    assert no_sleep == [2]


def test_wait_ready_raises_when_the_session_stops(respx_mock, client) -> None:
    respx_mock.get(f"{API}/services/{UUID}/info").respond(
        404, json={"message": "Session not found"}
    )

    with pytest.raises(SessionStoppedError, match="Session not found") as info:
        client.sessions.wait_ready(UUID)

    assert isinstance(info.value, NotFoundError)


def test_wait_ready_timeout(respx_mock, client) -> None:
    respx_mock.get(f"{API}/services/{UUID}/info").respond(
        json=load_fixture("session_compute_starting.json")
    )

    with pytest.raises(WaitTimeoutError):
        client.sessions.wait_ready(UUID, interval=3, timeout=5)


def test_wait_stopped(respx_mock, client) -> None:
    route = respx_mock.get(f"{API}/services/{UUID}/info")
    route.side_effect = [
        httpx.Response(200, json=load_fixture("session_compute_ready.json")),
        httpx.Response(404, json={"message": "Session not found"}),
    ]

    client.sessions.wait_stopped(UUID)

    assert route.call_count == 2
