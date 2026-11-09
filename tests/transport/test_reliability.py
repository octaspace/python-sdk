from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from octaspace import (
    APIConnectionError,
    APITimeoutError,
    ClientConfig,
    ConfigurationError,
    ConflictError,
    OctaSpaceClient,
    RateLimitError,
    ValidationError,
)
from octaspace._transport.httpx_transport import HttpxTransport
from octaspace.response import APIResponse

PRIMARY = "https://api.octa.space"
BACKUP = "https://api.octa.computer"


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []
    monkeypatch.setattr("octaspace._transport.httpx_transport.time.sleep", calls.append)
    return calls


def two_hosts() -> HttpxTransport:
    return HttpxTransport(ClientConfig(base_urls=[PRIMARY, BACKUP]))


def test_post_is_not_sent_to_another_host_after_a_timeout(respx_mock, sleeps) -> None:
    primary = respx_mock.post(f"{PRIMARY}/services/mr").mock(side_effect=httpx.ReadTimeout("slow"))
    backup = respx_mock.post(f"{BACKUP}/services/mr").respond(201, json={"uuid": "u"})

    with pytest.raises(APITimeoutError):
        two_hosts().post("/services/mr", body=[{"id": 0}])

    assert primary.call_count == 1
    assert backup.call_count == 0
    assert sleeps == []


def test_post_moves_to_another_host_when_it_cannot_connect(respx_mock) -> None:
    respx_mock.post(f"{PRIMARY}/services/mr").mock(side_effect=httpx.ConnectError("refused"))
    backup = respx_mock.post(f"{BACKUP}/services/mr").respond(201, json={"uuid": "u"})

    response = two_hosts().post("/services/mr", body=[{"id": 0}])

    assert response.data == {"uuid": "u"}
    assert backup.call_count == 1


def test_get_is_retried_after_a_connection_error(respx_mock, sleeps) -> None:
    route = respx_mock.get(f"{PRIMARY}/nodes")
    route.side_effect = [httpx.ConnectError("refused"), httpx.Response(200, json=[])]

    response = HttpxTransport(ClientConfig(max_retries=1)).get("/nodes")

    assert response.data == []
    assert route.call_count == 2
    assert len(sleeps) == 1


def test_post_is_not_retried_after_a_timeout(respx_mock, sleeps) -> None:
    route = respx_mock.post(f"{PRIMARY}/services/x/stop").mock(
        side_effect=httpx.ReadTimeout("slow")
    )

    with pytest.raises(APITimeoutError):
        HttpxTransport(ClientConfig(max_retries=2)).post("/services/x/stop")

    assert route.call_count == 1
    assert sleeps == []


def test_protocol_errors_raise_a_connection_error(respx_mock) -> None:
    respx_mock.get(f"{PRIMARY}/nodes").mock(side_effect=httpx.RemoteProtocolError("dropped"))

    with pytest.raises(APIConnectionError):
        HttpxTransport(ClientConfig(max_retries=0)).get("/nodes")


def test_retry_after_longer_than_the_limit_raises_at_once(respx_mock, sleeps) -> None:
    route = respx_mock.get(f"{PRIMARY}/nodes").respond(429, headers={"Retry-After": "120"})

    with pytest.raises(RateLimitError) as info:
        HttpxTransport(ClientConfig(max_retries=2, max_retry_after=60)).get("/nodes")

    assert info.value.retry_after == 120
    assert route.call_count == 1
    assert sleeps == []


def test_retry_after_accepts_an_http_date() -> None:
    when = datetime.now(UTC) + timedelta(seconds=30)
    headers = httpx.Headers({"Retry-After": format_datetime(when, usegmt=True)})
    response = APIResponse(status_code=429, headers=headers, body=b"")

    assert response.retry_after is not None
    assert 28 <= response.retry_after <= 30


def test_retry_after_in_the_past_or_invalid() -> None:
    past = APIResponse(429, httpx.Headers({"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}), b"")
    no_zone = APIResponse(
        429, httpx.Headers({"Retry-After": "Wed, 21 Oct 2015 07:28:00 -0000"}), b""
    )
    invalid = APIResponse(429, httpx.Headers({"Retry-After": "soon"}), b"")

    assert past.retry_after == 0
    assert no_zone.retry_after == 0
    assert invalid.retry_after is None


@pytest.mark.parametrize(("status", "error"), [(400, ValidationError), (409, ConflictError)])
def test_status_errors(respx_mock, status: int, error: type[Exception]) -> None:
    respx_mock.post(f"{PRIMARY}/services/mr").respond(
        status, json={"message": "Insufficient balance"}
    )

    with pytest.raises(error, match="Insufficient balance"):
        HttpxTransport(ClientConfig(max_retries=0)).post("/services/mr")


def test_api_key_is_not_in_the_repr() -> None:
    config = ClientConfig(api_key="secret-token")

    assert "secret-token" not in repr(config)
    assert "secret-token" not in repr(OctaSpaceClient(config=config).config)


def test_invalid_environment_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTA_READ_TIMEOUT", "fast")

    with pytest.raises(ConfigurationError, match="OCTA_READ_TIMEOUT"):
        ClientConfig.from_env()


def test_configuration_error_is_a_value_error() -> None:
    with pytest.raises(ValueError):
        ClientConfig(pool_size=-1)
    with pytest.raises(ConfigurationError):
        OctaSpaceClient(unknown_option=1)
