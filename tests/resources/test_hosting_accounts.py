from __future__ import annotations

import pytest

from helpers import API, load_fixture, sent_json
from octaspace import NotFoundError, format_usd


def test_balance(respx_mock, client) -> None:
    respx_mock.get(f"{API}/accounts/balance").respond(json=load_fixture("account_balance.json"))

    balance = client.accounts.balance()

    assert balance["currency"] == "USD"
    assert format_usd(balance["balance"]).startswith("$")


def test_nodes_normalize_null_strings(respx_mock, client) -> None:
    respx_mock.get(f"{API}/hosting/nodes").respond(json=load_fixture("hosting_nodes.json"))

    nodes = client.hosting.nodes()

    gpus = [gpu for node in nodes for gpu in node["system"].get("gpus", [])]
    assert "null" not in [value for gpu in gpus for value in gpu.values()]


def test_get_node(respx_mock, client) -> None:
    node = load_fixture("hosting_nodes.json")[0]
    respx_mock.get(f"{API}/hosting/nodes/7KQ4-M2XD-4").respond(json=node)
    respx_mock.get(f"{API}/hosting/nodes/3HW9-P6TR-8").respond(
        404, json={"message": "Node not found"}
    )

    assert client.hosting.get("7KQ4-M2XD-4")["number"] == node["number"]
    with pytest.raises(NotFoundError):
        client.hosting.get("3HW9-P6TR-8")


def test_set_prices(respx_mock, client) -> None:
    route = respx_mock.patch(f"{API}/hosting/nodes/7KQ4-M2XD-4/prices").respond(204)

    client.hosting.set_prices("7KQ4-M2XD-4", base=250_000, min_rent_minutes=0)

    assert sent_json(route) == {"base": 250_000, "min_rent_minutes": 0}


def test_set_prices_checks_values(respx_mock, client) -> None:
    route = respx_mock.patch(f"{API}/hosting/nodes/7KQ4-M2XD-4/prices").respond(204)

    with pytest.raises(TypeError, match="at least one"):
        client.hosting.set_prices("7KQ4-M2XD-4")
    with pytest.raises(TypeError, match="base must be an integer"):
        client.hosting.set_prices("7KQ4-M2XD-4", base=0.25)  # type: ignore[arg-type]

    assert route.call_count == 0


def test_maintenance(respx_mock, client) -> None:
    on = respx_mock.put(f"{API}/hosting/nodes/7KQ4-M2XD-4/maintenance").respond(204)
    off = respx_mock.delete(f"{API}/hosting/nodes/7KQ4-M2XD-4/maintenance").respond(204)

    assert client.hosting.start_maintenance("7KQ4-M2XD-4") is None
    assert client.hosting.end_maintenance("7KQ4-M2XD-4") is None
    assert (on.call_count, off.call_count) == (1, 1)
