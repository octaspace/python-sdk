from __future__ import annotations

from typing import cast

from octaspace import OctaSpaceClient
from octaspace.hooks import RequestContext
from octaspace.response import APIResponse


def test_request_and_response_hooks(respx_mock) -> None:
    captured_request: list[RequestContext] = []
    captured_response: list[APIResponse] = []

    respx_mock.get("https://api.octa.space/network").respond(json={"at": 1})

    with OctaSpaceClient(
        api_key="test_key",
        max_retries=0,
        on_request=captured_request.append,
        on_response=captured_response.append,
    ) as client:
        response = client.network.info()

    assert response == {"at": 1}
    assert captured_request[0].method == "get"
    assert captured_request[0].path == "/network"
    assert captured_response[0].status_code == 200
    assert cast(dict[str, int], captured_response[0].data)["at"] == 1
