from __future__ import annotations

import httpx
import pytest

from octaspace import APIError, AuthenticationError, ClientConfig
from octaspace._transport.httpx_transport import HttpxTransport, normalize_api_key
from octaspace.errors import APIConnectionError, APITimeoutError, RateLimitError

API = "https://api.octa.space"


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []
    monkeypatch.setattr("octaspace._transport.httpx_transport.time.sleep", calls.append)
    return calls


def test_sends_bearer_key_and_app_header(respx_mock) -> None:
    route = respx_mock.get(f"{API}/accounts/balance").respond(json={"balance": 1})
    transport = HttpxTransport(ClientConfig(api_key="octa_ak_test", max_retries=0))

    transport.request("GET", "/accounts/balance")

    headers = route.calls.last.request.headers
    assert headers["Authorization"] == "Bearer octa_ak_test"
    assert headers["X-OCTA-APP"] == "python-sdk"
    assert headers["Accept"] == "application/json"
    assert headers["User-Agent"].startswith("octaspace-python/")


def test_normalize_api_key() -> None:
    assert normalize_api_key(" Bearer octa_ak_x ") == "octa_ak_x"
    assert normalize_api_key("  ") is None
    assert normalize_api_key(None) is None


def test_required_auth_without_a_key_fails_before_sending(respx_mock) -> None:
    route = respx_mock.get(f"{API}/sessions").respond(json=[])

    with pytest.raises(AuthenticationError, match="Account → Credentials → API Keys"):
        HttpxTransport(ClientConfig()).request("GET", "/sessions")

    assert route.call_count == 0


def test_optional_and_none_auth(respx_mock) -> None:
    route = respx_mock.get(f"{API}/x").respond(json=[])
    anonymous = HttpxTransport(ClientConfig())
    keyed = HttpxTransport(ClientConfig(api_key="octa_ak_test"))

    anonymous.request("GET", "/x", auth="optional")
    assert "Authorization" not in route.calls.last.request.headers
    keyed.request("GET", "/x", auth="optional")
    assert route.calls.last.request.headers["Authorization"] == "Bearer octa_ak_test"
    keyed.request("GET", "/x", auth="none")
    assert "Authorization" not in route.calls.last.request.headers


def test_401_with_a_key_of_another_format_explains(respx_mock) -> None:
    respx_mock.get(f"{API}/sessions").respond(401, json={"message": "Invalid bearer token"})

    with pytest.raises(AuthenticationError, match='start with "octa_ak_"'):
        HttpxTransport(ClientConfig(api_key="0123abcd", max_retries=0)).request("GET", "/sessions")


def test_query_drops_none_values(respx_mock) -> None:
    route = respx_mock.get(f"{API}/stats/mining").respond(json={})

    HttpxTransport(ClientConfig()).request(
        "GET", "/stats/mining", params={"role": "cpu", "days": None}, auth="none"
    )

    assert str(route.calls.last.request.url) == f"{API}/stats/mining?role=cpu"


def test_body_is_json(respx_mock) -> None:
    route = respx_mock.post(f"{API}/services/render").respond(201, json={"uuid": "u"})

    response = HttpxTransport(ClientConfig(api_key="octa_ak_test")).request(
        "POST", "/services/render", body={"node_number": "7KQ4-M2XD-4"}
    )

    assert response.data == {"uuid": "u"}
    request = route.calls.last.request
    assert request.headers["Content-Type"] == "application/json"
    assert request.content == b'{"node_number":"7KQ4-M2XD-4"}'


def test_empty_body_is_none(respx_mock) -> None:
    respx_mock.put(f"{API}/hosting/nodes/7KQ4-M2XD-4/maintenance").respond(204)
    transport = HttpxTransport(ClientConfig(api_key="octa_ak_test"))

    response = transport.request("PUT", "/hosting/nodes/7KQ4-M2XD-4/maintenance")

    assert response.data is None


def test_success_that_is_not_json_raises(respx_mock) -> None:
    respx_mock.get(f"{API}/network").respond(200, html="<html>captive portal</html>")

    with pytest.raises(APIError, match="not valid JSON") as info:
        HttpxTransport(ClientConfig()).request("GET", "/network", auth="none")

    assert info.value.status_code == 200


def test_records_the_rate_limit(respx_mock) -> None:
    respx_mock.get(f"{API}/network").respond(
        json={},
        headers={"RateLimit-Limit": "60", "RateLimit-Remaining": "59", "RateLimit-Reset": "60"},
    )
    transport = HttpxTransport(ClientConfig())
    assert transport.rate_limit is None

    transport.request("GET", "/network", auth="none")

    assert transport.rate_limit is not None
    assert (transport.rate_limit.limit, transport.rate_limit.remaining) == (60, 59)


def test_get_is_retried_on_503_not_on_500(respx_mock, sleeps) -> None:
    route = respx_mock.get(f"{API}/network")
    route.side_effect = [httpx.Response(503, json={}), httpx.Response(200, json={})]
    HttpxTransport(ClientConfig(max_retries=1)).request("GET", "/network", auth="none")
    assert route.call_count == 2

    other = respx_mock.get(f"{API}/stats/gpu/locations").respond(500, json={"message": "boom"})
    with pytest.raises(APIError, match="boom"):
        HttpxTransport(ClientConfig(max_retries=2)).request(
            "GET", "/stats/gpu/locations", auth="none"
        )
    assert other.call_count == 1


def test_honors_retry_after(respx_mock, sleeps) -> None:
    route = respx_mock.get(f"{API}/network").respond(
        429, json={"message": "Too many requests"}, headers={"Retry-After": "7"}
    )

    with pytest.raises(RateLimitError) as info:
        HttpxTransport(ClientConfig(max_retries=1)).request("GET", "/network", auth="none")

    assert sleeps == [7.0]
    assert route.call_count == 2
    assert info.value.retry_after == 7


def test_idempotent_post_is_retried(respx_mock, sleeps) -> None:
    route = respx_mock.post(f"{API}/services/u/stop")
    route.side_effect = [httpx.ReadTimeout("slow"), httpx.Response(202, json={"uuid": "u"})]
    transport = HttpxTransport(ClientConfig(api_key="octa_ak_test", max_retries=1))

    response = transport.request("POST", "/services/u/stop", idempotent=True)

    assert response.data == {"uuid": "u"}
    assert route.call_count == 2


def test_fails_over_on_connection_error(respx_mock) -> None:
    respx_mock.get("https://bad.example.com/network").mock(side_effect=httpx.ConnectError("x"))
    respx_mock.get(f"{API}/network").respond(json={})
    transport = HttpxTransport(
        ClientConfig(base_urls=["https://bad.example.com", API], max_retries=0)
    )

    assert transport.request("GET", "/network", auth="none").is_success
    assert transport.transport_stats()["rotator"]["total"] == 2


def test_raises_when_all_hosts_fail(respx_mock) -> None:
    respx_mock.get("https://a.example.com/network").mock(side_effect=httpx.ConnectError("x"))
    respx_mock.get("https://b.example.com/network").mock(side_effect=httpx.ReadTimeout("y"))
    transport = HttpxTransport(
        ClientConfig(base_urls=["https://a.example.com", "https://b.example.com"], max_retries=0)
    )

    with pytest.raises((APIConnectionError, APITimeoutError)):
        transport.request("GET", "/network", auth="none")
