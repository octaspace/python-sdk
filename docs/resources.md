# Resources

[← Back to README](../README.md)

**On this page:** [Conventions](#conventions) · [Compute](#compute) · [Render](#render) ·
[VPN](#vpn) · [Hosting](#hosting) · [Accounts](#accounts) · [Network](#network) ·
[Stats](#stats)

Sessions have [their own guide](sessions.md). The examples assume a client
created as in the [Quick start](../README.md#quick-start):

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
```

## Conventions

| Concept | In the SDK |
| --- | --- |
| Money | An integer number of micro-USD, millionths of a US dollar (`1` = $0.000001): prices, charges, the balance. `format_usd(250000)` returns `"$0.250000"`; `micro_usd_to_usd()` returns a `Decimal`, `usd_to_micro_usd()` converts back. |
| Node | Identified by its node number, for example `7KQ4-M2XD-4`. Case, dashes and spaces are ignored. |
| Network speed | Whole Mbit/s in `net_down_mbps` / `net_up_mbps`; `0` if not measured. |
| Time | `started_at` of a session and log `ts` are Unix milliseconds; statistics timestamps are Unix seconds. Methods that take a time accept Unix seconds or a `datetime`. |
| Optional arguments | An argument left as `None` is not sent. `False` is sent as is. |
| Responses | Methods return the API's JSON as `dict` and `list` objects, described by the `TypedDict` classes in `octaspace.types`. Keys that the types do not list are kept as well. Optional keys can be missing: read them with `.get()`. |

## Compute

Rent a machine and run your own container on it.

### List machines

```python
from octaspace import format_usd

for m in client.compute.list():
    print(m["node_number"], m["city"], m["cpu_cores"], format_usd(m["base_price"]))
```

A `ComputeMachine` has its location, CPU, memory, disk, GPUs, network speed,
operating system, reliability and prices:

| Field | Meaning |
| --- | --- |
| `base_price` | Per hour of rent |
| `storage_price` | Per GB of disk per hour |
| `traffic_price` | Per GB of traffic |
| `min_rent_minutes` | Minimum rent, see below; `0` if none |

> [!NOTE]
> **Minimum rent.** If the node owner set a minimum rent, a session stopped
> sooner is charged as if it ran that long. It is not charged if the node fails.

The listing also works without an API key, but is then refreshed about once an
hour; with a key it is at most 10 seconds old.

### Apps

An app is a ready-made image with its settings. `compute.apps()` lists the
official apps and, with an API key, your own (`personal` is `True`):

```python
apps = client.compute.apps()
ubuntu = next(app for app in apps if app["name"] == "Ubuntu 24.04 LTS")

client.compute.start(
    "7KQ4-M2XD-4",
    ubuntu["image"],
    app=ubuntu["uuid"],
    disk_size=ubuntu.get("extra", {}).get("min_disk_size", 10),
)
```

| Field | Meaning |
| --- | --- |
| `uuid` | Pass as `app` to `compute.start()`; the image is still required |
| `ports`, `http_ports` | Ports the app exposes |
| `extra["min_disk_size"]` | Disk the app needs, GB. Not enforced: a smaller `disk_size` is accepted, and the app may run out of space |
| `startup_script`, `envs` | Only on your own apps |

The list also works without an API key, without your own apps.

### Start a session

```python
result = client.compute.start(
    "7KQ4-M2XD-4",
    "ubuntu:24.04",
    disk_size=20,  # GB
    entrypoint="sh -c",
    args='"sleep infinity"',
    ssh=True,
)
uuid = result["uuid"]
```

The node number and the image are required. Arguments you leave out are not
sent and take their defaults:

| Argument | Meaning | Default |
| --- | --- | --- |
| `disk_size` | Disk size, GB | `1` |
| `envs` | Environment variables: up to 64; names of letters, digits and `_`, not starting with a digit; values up to 4 KiB | none |
| `ports` | TCP/UDP container ports to expose | none |
| `http_ports` | HTTP container ports to expose with a public URL, up to 10 | none |
| `entrypoint`, `args` | Replace the image's `ENTRYPOINT` and `CMD`, one line each. Nothing is expanded: use `sh -c '…'` for `$VAR`, `*` or `&&` | the image's own |
| `ssh` | Web terminal and SSH access | the app's setting, off without one |
| `fm` | Web file manager. It has no login: anyone with its URL can read the files | the app's setting, off without one |
| `startup_script` | Script run as root once the container is up; output goes to `/var/log/onstart.log` | none |
| `app` | App UUID, see [Apps](#apps) | none |

Pass `ssh=False` or `fm=False` to turn off SSH or the file manager that an app
enables.

`start` returns as soon as the session is created, while its container is still
being set up. Wait for it with
[`sessions.wait_ready()`](sessions.md#wait-until-ready). A rejected request,
for example for an insufficient balance, raises a `ValidationError` with the
reason.

### Start several sessions

```python
results = client.compute.start_batch(
    [
        {"id": "a", "node_number": "7KQ4-M2XD-4", "image": "ubuntu:24.04"},
        {"id": "b", "node_number": "3HW9-P6TR-8", "image": "ubuntu:24.04"},
    ]
)
for r in results:
    if r["status"] == 0:
        print(r["id"], "started", r["uuid"])
    else:
        print(r["id"], "failed:", r["reason"])
```

Each item takes the arguments of `start()`. Items are checked one by one: one
that fails does not stop the others. Results come in the order of the items.
An item without `id` gets its position in the list; two items with the same
`id`, or an item with an unknown key, raise a `TypeError` before anything is
sent.

### Restart a session

```python
client.compute.restart(uuid)  # keep the parameters
```

`restart` recreates the container on the same node; the session keeps running,
with the same `uuid` and prices. Without arguments the session restarts with the
parameters it was started with. Follow the restart with `sessions.get()`.

> [!WARNING]
> Arguments you pass **replace** the session's parameters as a whole; they are
> not merged. Every argument you leave out takes its default: `disk_size`
> becomes 1 GB, and `envs`, ports, `startup_script`, `ssh` and `fm` are dropped.
> Include everything the session needs:
>
> ```python
> client.compute.restart(
>     uuid,
>     disk_size=20,
>     entrypoint="sh -c",
>     args='"sleep infinity"',
>     ssh=True,
> )
> ```

The node, image and app cannot be changed. If the new parameters cannot be
applied, the session stops.

| Error | When |
| --- | --- |
| `ConflictError` | The session is already starting or restarting |
| `RateLimitError` | The session was restarted too recently; wait `retry_after` seconds. A session can be restarted once in 5 minutes and 6 times an hour |

## Render

Rent a render node.

```python
nodes = client.render.list()

uuid = client.render.start("7KQ4-M2XD-4")["uuid"]

results = client.render.start_batch(
    [
        {"id": "a", "node_number": "7KQ4-M2XD-4"},
        {"id": "b", "node_number": "3HW9-P6TR-8"},
    ]
)
```

A `RenderMachine` is a node with an NVIDIA GPU, its Blender score and
`base_price` per hour. The node renders for your account until you stop the
session.

When render is temporarily unavailable, `start` raises a
`ServiceUnavailableError`, while `start_batch` reports it for each item
(`status` 1).

## VPN

Rent a VPN on a node, billed by traffic.

```python
from pathlib import Path

from octaspace import is_vpn_session

node = next(n for n in client.vpn.list() if "wg" in n["protocols"])
uuid = client.vpn.start(node["node_number"], "wg")["uuid"]

session = client.sessions.wait_ready(uuid)
config = session.get("config") if is_vpn_session(session) else None
if isinstance(config, str):
    # a WireGuard config: import it into the client
    path = Path("octa.conf")
    path.touch(mode=0o600)
    path.write_text(config)
```

A `VpnMachine` has its location, network speed, `traffic_price` per GB and
`protocols`: the protocols that passed an end-to-end check on that node.

| `subkind` | The session's `config` |
| --- | --- |
| `wg` | WireGuard config file |
| `awg` | AmneziaWG config file |
| `reality` | VLESS Reality link |
| `http_proxy` | A dict with the proxy's `ip` and `port` and its login (`username`, `password`, HTTP Basic). The proxy lets in only the IP address the `start` request came from |

Pick a `subkind` from the node's `protocols`. A protocol the node did not pass
raises a `ValidationError` (`Node's VPN did not pass the connection check`);
nothing is started or charged.

- One VPN session per node: a second one on the same node raises a
  `ValidationError` (`You already have a VPN session on this node`).
- `config` of a ready session is **a credential**: a WireGuard config holds the
  private key, and a proxy's has its password. Do not log it.
- VPN sessions have no logs, and a node running one stays `idle` in
  `hosting.nodes()`.
- Stop the session with `client.sessions.stop(uuid)`; until then it is charged
  for traffic.

The listing also works without an API key, but is then refreshed about once an
hour; with a key it is at most 10 seconds old.

## Hosting

The nodes you host, their prices and maintenance mode.

```python
for n in client.hosting.nodes():
    print(n["number"], n["status"], format_usd(n["prices"]["base"]), n.get("uptime_percent"))

node = client.hosting.get("7KQ4-M2XD-4")
```

`nodes` lists your nodes that are online, with their status (`idle`, `rented`,
`verification`, `benchmark`), the services they are offered for, prices,
hardware, location and uptime. A node that runs only VPN sessions stays `idle`.

`get` returns one of your online nodes. It raises a `NotFoundError` for a node
that is offline, does not exist or is not yours.

### Set prices

```python
from octaspace import usd_to_micro_usd

client.hosting.set_prices(
    "7KQ4-M2XD-4",
    base=usd_to_micro_usd("0.25"),  # $0.25 per hour
    min_rent_minutes=15,
)
```

Only the prices you pass change; at least one is required. The listings show
the new prices within a few seconds.

| Argument | Meaning | Range |
| --- | --- | --- |
| `base` | Charged for every hour the node is rented | $0.0001 – $1000 |
| `storage` | Charged per hour for each GB of disk the renter allocates | $0 – $1000 |
| `traffic` | Charged for each GB of network traffic a rental uses | $0.0001 – $1000 |
| `min_rent_minutes` | Minimum rent of a compute session | 0 – 60 minutes; `0` turns it off |

Prices are integer micro-USD; a value that is not an integer raises a
`TypeError` before the request is sent. A value out of range raises a
`ValidationError`, an unknown node a `NotFoundError`.

### Maintenance mode

```python
client.hosting.start_maintenance("7KQ4-M2XD-4")
# ... work on the node ...
client.hosting.end_maintenance("7KQ4-M2XD-4")
```

A node in maintenance mode is not offered for new rentals; running sessions go
on and their renters are notified. It works for a node that is offline too, and
calling either method again changes nothing. `maintenance` of a hosted node
tells whether it is on.

## Accounts

```python
balance = client.accounts.balance()
print(format_usd(balance["balance"]))  # $12.500000
```

The balance already includes what running sessions have used and becomes
negative when they use more than the account has. A recent charge or deposit
can take a moment to appear.

## Network

Platform statistics. No API key is needed.

```python
from datetime import UTC, datetime, timedelta

from octaspace import network_history_points

info = client.network.info()
print(info["nodes"]["online"], info["sessions"]["running"], datetime.fromtimestamp(info["at"], UTC))

history = client.network.history(
    start=datetime.now(UTC) - timedelta(days=7),
    step=6 * 3600,  # seconds
)
for p in network_history_points(history):
    print(datetime.fromtimestamp(p["ts"], UTC), p["nodes_online"], p["gpus_rented"])
```

| Method | Returns |
| --- | --- |
| `info` | Nodes, capacity, sessions, users, rendered frames and VPN nodes now |
| `history` | Nodes, GPUs, TFLOPS, users and sessions over time; the last day with hourly points by default. Each value is the average over its step, so it can be fractional. `step` is at least 300 seconds; a range has at most 2000 points. `network_history_points()` turns it into one dict per point. |

## Stats

GPU market and mining statistics. No API key is needed.

```python
from octaspace import gpu_history_points

market = client.stats.gpu_current(verified="yes")
for g in market["gpus"]:
    print(g["model"], g["available"], g["rented"], g["available_price"]["p50"])

history = client.stats.gpu_history(
    gpu_name=["NVIDIA GeForce RTX 4090"],
    start=datetime.now(UTC) - timedelta(days=7),
    step=6 * 3600,  # seconds
)
for p in gpu_history_points(history["NVIDIA GeForce RTX 4090"]):
    print(datetime.fromtimestamp(p["ts"], UTC), p["rented"], p["rented_price"]["p50"])

locations = client.stats.gpu_locations()

mining = client.stats.mining(role="gpu", days=30)
for m in mining["miners"]:
    print(m["label"] or m["name"], m["gpu_hours"])
```

| Method | Returns |
| --- | --- |
| `gpu_current` | Per GPU model: the number of GPUs (not nodes), how many are rented, memory, performance, and price percentiles in micro-USD per GPU-hour. A percentile is `None` when there is no price. |
| `gpu_history` | The same over time, by model; the last day with hourly points by default. `step` is at least 300 seconds; a range has at most 2000 points. `gpu_history_points()` turns one model's history into one dict per point. |
| `gpu_locations` | The number of GPUs by city and model |
| `mining` | Miners, algorithms and pools of the platform's mining sessions, most used first, and the miners per day. `role` is `gpu` (default) or `cpu`; `days` is 1 – 365 (default 30). |

`verified` selects the nodes the statistics cover: `"all"`, `"yes"` (verified
only) or `"no"`.
