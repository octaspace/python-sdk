from __future__ import annotations

from datetime import UTC, datetime

from helpers import API, load_fixture
from octaspace import gpu_history_points, network_history_points


def test_network_info_never_sends_the_key(respx_mock, client) -> None:
    route = respx_mock.get(f"{API}/network").respond(json=load_fixture("network.json"))

    info = client.network.info()

    assert "Authorization" not in route.calls.last.request.headers
    assert info["nodes"]["online"] >= 0


def test_network_history(respx_mock, anonymous) -> None:
    history = load_fixture("network_history.json")
    route = respx_mock.get(f"{API}/network/history").respond(json=history)

    result = anonymous.network.history(start=datetime(2026, 11, 1, tzinfo=UTC), step=3600)
    points = network_history_points(result)

    params = route.calls.last.request.url.params
    assert dict(params) == {"start": "1793491200", "step": "3600"}
    assert len(points) == len(history["timestamps"])
    assert points[0]["nodes_online"] == history["nodes_online"][0]


def test_gpu_current_normalizes(respx_mock, anonymous) -> None:
    route = respx_mock.get(f"{API}/stats/gpu/current").respond(
        json=load_fixture("stats_gpu_current.json")
    )

    current = anonymous.stats.gpu_current(verified="yes")

    assert route.calls.last.request.url.params["verified"] == "yes"
    arc = current["gpus"][1]
    assert arc["rented_price"]["p50"] is None and arc.get("tflops") is None
    assert current["gpus"][0].get("memory_mb") == 24576


def test_gpu_history(respx_mock, anonymous) -> None:
    route = respx_mock.get(f"{API}/stats/gpu/history").respond(
        json=load_fixture("stats_gpu_history.json")
    )

    history = anonymous.stats.gpu_history(gpu_name=["Arc B580", "NVIDIA GeForce RTX 3090"])
    points = gpu_history_points(history["NVIDIA GeForce RTX 3090"])

    assert route.calls.last.request.url.params["gpu_name"] == "Arc B580,NVIDIA GeForce RTX 3090"
    assert points[0]["ts"] == history["NVIDIA GeForce RTX 3090"]["timestamps"][0]
    assert set(points[0]["rented_price"]) == {"p10", "p25", "p50", "p75", "p90"}
    assert history["Arc B580"].get("tflops") is None


def test_gpu_locations_and_mining(respx_mock, anonymous) -> None:
    respx_mock.get(f"{API}/stats/gpu/locations").respond(
        json=load_fixture("stats_gpu_locations.json")
    )
    route = respx_mock.get(f"{API}/stats/mining").respond(json=load_fixture("stats_mining.json"))

    assert anonymous.stats.gpu_locations()[0]["gpus"] >= 0
    mining = anonymous.stats.mining(role="gpu", days=7)

    assert dict(route.calls.last.request.url.params) == {"role": "gpu", "days": "7"}
    assert "null" not in [row["label"] for row in mining["miners"]]
    assert "from" in mining
