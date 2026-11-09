from __future__ import annotations

from octaspace._transport.httpx_transport import HttpxTransport
from octaspace.config import ClientConfig


def test_transport_put_delete_and_custom_headers(respx_mock) -> None:
    put_route = respx_mock.put("https://api.octa.space/nodes/1").respond(json={"updated": True})
    delete_route = respx_mock.delete("https://api.octa.space/idle_jobs/1").respond(
        json={"deleted": True}
    )
    transport = HttpxTransport(ClientConfig(api_key="test_key", max_retries=0))

    assert (
        transport.put("/nodes/1", body={"gpu_hour": 0.5}, headers={"X-Test": "1"}).data["updated"]
        is True
    )
    assert transport.delete("/idle_jobs/1", params={"force": "1"}).data["deleted"] is True
    assert put_route.calls.last.request.headers["X-Test"] == "1"
    assert delete_route.calls.last.request.headers["Connection"] == "close"
    assert transport.transport_stats()["url"] == "https://api.octa.space"
    transport.close()
