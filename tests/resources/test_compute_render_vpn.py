from __future__ import annotations

import pytest

from helpers import API, load_fixture, sent_json
from octaspace import ServiceUnavailableError, ValidationError


def test_compute_list_works_without_a_key_and_normalizes(respx_mock, anonymous) -> None:
    route = respx_mock.get(f"{API}/services/compute").respond(
        json=load_fixture("services_compute.json")
    )

    machines = anonymous.compute.list()

    assert "Authorization" not in route.calls.last.request.headers
    assert machines[0]["node_number"] == "3HW9-P6TR-8"
    assert machines[0]["os_version"] == "Ubuntu 24.04"
    gpu = machines[2]["gpus"][0]
    assert gpu.get("power_limit") is None and gpu.get("mem_clock") is None


def test_compute_list_sends_the_key_when_there_is_one(respx_mock, client) -> None:
    route = respx_mock.get(f"{API}/services/compute").respond(json=[])

    client.compute.list()

    assert route.calls.last.request.headers["Authorization"] == "Bearer octa_ak_test"


def test_gpu_integers_given_as_strings(respx_mock, anonymous) -> None:
    gpu = {"model": "X", "mem_total_mb": "8192", "pcie_link_gen": "", "power_limit": "n/a"}
    respx_mock.get(f"{API}/services/render").respond(json=[{"node_number": "N", "gpus": [gpu]}])

    [machine] = anonymous.render.list()

    assert machine["gpus"][0] == {
        "model": "X",
        "mem_total_mb": 8192,
        "pcie_link_gen": None,
        "power_limit": None,
    }


def test_compute_apps_normalizes_only_category_and_description(respx_mock, anonymous) -> None:
    apps = load_fixture("compute_apps.json")
    apps[1]["entrypoint"] = "null"
    respx_mock.get(f"{API}/compute/apps").respond(json=apps)

    result = anonymous.compute.apps()

    assert result[1].get("category") is None
    assert result[1].get("entrypoint") == "null"
    assert result[0]["personal"] is False


def test_compute_start_sends_only_given_fields(respx_mock, client) -> None:
    route = respx_mock.post(f"{API}/services/compute").respond(201, json={"uuid": "u1"})

    result = client.compute.start(
        "7KQ4-M2XD-4", "ubuntu:24.04", disk_size=20, ports=(8080,), ssh=False
    )

    assert result == {"uuid": "u1"}
    assert sent_json(route) == {
        "node_number": "7KQ4-M2XD-4",
        "image": "ubuntu:24.04",
        "disk_size": 20,
        "ports": [8080],
        "ssh": False,
    }


def test_compute_start_is_not_retried(respx_mock) -> None:
    from octaspace import OctaSpaceClient

    route = respx_mock.post(f"{API}/services/compute").respond(503, json={})
    with (
        OctaSpaceClient(api_key="octa_ak_test", max_retries=3) as client,
        pytest.raises(ServiceUnavailableError),
    ):
        client.compute.start("7KQ4-M2XD-4", "ubuntu:24.04")

    assert route.call_count == 1


def test_compute_start_rejection(respx_mock, client) -> None:
    respx_mock.post(f"{API}/services/compute").respond(
        400, json={"message": "Insufficient balance"}
    )

    with pytest.raises(ValidationError, match="Insufficient balance"):
        client.compute.start("7KQ4-M2XD-4", "ubuntu:24.04")


def test_compute_start_batch(respx_mock, client) -> None:
    results = [{"id": "a", "status": 0, "uuid": "u1"}, {"id": 1, "status": 1, "reason": "No"}]
    route = respx_mock.post(f"{API}/services/compute").respond(json=results)

    response = client.compute.start_batch(
        [
            {"id": "a", "node_number": "7KQ4-M2XD-4", "image": "ubuntu:24.04"},
            {"node_number": "3HW9-P6TR-8", "image": "ubuntu:24.04", "ssh": True},
        ]
    )

    assert response == results
    assert sent_json(route) == [
        {"id": "a", "node_number": "7KQ4-M2XD-4", "image": "ubuntu:24.04"},
        {"id": 1, "node_number": "3HW9-P6TR-8", "image": "ubuntu:24.04", "ssh": True},
    ]


def test_compute_start_batch_refuses_duplicates_and_unknown_fields(respx_mock, client) -> None:
    route = respx_mock.post(f"{API}/services/compute").respond(json=[])

    with pytest.raises(TypeError, match="Duplicate batch id 1"):
        client.compute.start_batch(
            [
                {"node_number": "A", "image": "i", "id": 1},
                {"node_number": "B", "image": "i"},
            ]
        )
    with pytest.raises(TypeError, match="http_port"):
        client.compute.start_batch([{"node_number": "A", "image": "i", "http_port": [80]}])  # type: ignore[typeddict-unknown-key]

    assert route.call_count == 0


def test_compute_restart(respx_mock, client) -> None:
    route = respx_mock.post(f"{API}/services/compute/u1/restart").respond(202, json={"uuid": "u1"})

    assert client.compute.restart("u1") == {"uuid": "u1"}
    assert route.calls.last.request.content == b""

    client.compute.restart("u1", disk_size=20, envs={"A": "1"})
    assert sent_json(route) == {"disk_size": 20, "envs": {"A": "1"}}


def test_render_start_and_batch(respx_mock, client) -> None:
    route = respx_mock.post(f"{API}/services/render").respond(201, json={"uuid": "u1"})

    assert client.render.start("7KQ4-M2XD-4") == {"uuid": "u1"}
    assert sent_json(route) == {"node_number": "7KQ4-M2XD-4"}

    route.respond(json=[{"id": 0, "status": 0, "uuid": "u1"}])
    client.render.start_batch([{"node_number": "7KQ4-M2XD-4"}])
    assert sent_json(route) == [{"id": 0, "node_number": "7KQ4-M2XD-4"}]


def test_render_list_fixture(respx_mock, anonymous) -> None:
    respx_mock.get(f"{API}/services/render").respond(json=load_fixture("services_render.json"))

    machines = anonymous.render.list()

    assert machines[0]["blender_score"] > 0


def test_vpn_list_and_start(respx_mock, client) -> None:
    respx_mock.get(f"{API}/services/vpn").respond(json=load_fixture("services_vpn.json"))
    route = respx_mock.post(f"{API}/services/vpn").respond(201, json={"uuid": "v1"})

    [node] = client.vpn.list()
    result = client.vpn.start(node["node_number"], "wg")

    assert "wg" in node["protocols"]
    assert result == {"uuid": "v1"}
    assert sent_json(route) == {"node_number": "7KQ4-M2XD-4", "subkind": "wg"}
