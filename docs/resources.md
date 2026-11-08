# Resources

[← Back to README](../README.md)

**On this page:** [Conventions](#conventions) ·
[Machine rental](#machine-rental) · [VPN](#vpn) · [Render](#render) ·
[Sessions](#sessions) · [Applications](#applications) · [Nodes](#nodes) ·
[Idle jobs](#idle-jobs) · [Accounts](#accounts) · [Network](#network)

The examples assume a client created as in the
[Quick start](../README.md#quick-start):

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
```

## Conventions

| Concept | In the API |
| --- | --- |
| Results | Every method returns an `APIResponse`; `.data` holds the parsed JSON (a `dict` or a `list`). Field names are those of the [API reference](https://api.octa.space/api-docs). |
| Node | Identified by an integer `node_id`, for example `312`. |
| Session | Identified by its UUID, for example `96e33710-ec12-11ed-8588-fa163e49e8aa`. |
| Balance and charges | Integers in Wei of OCTA: 1 OCTA = 10¹⁸ Wei. |
| Sizes | `disk_size` in GB; `free_disk`, `total_memory` and traffic (`rx`, `tx`) in bytes. |
| Time | `started_at` in Unix milliseconds, `duration` in seconds. |

## Machine rental

Rent a machine and run your own container on it. In the dashboard:
**Marketplace → Compute**.

### List machines

```python
for machine in client.services.mr.list().data:
    print(machine["node_id"], machine["city"], machine["cpu_cores"], machine["free_disk"])
```

Also works without an API token.

### Start a session

```python
response = client.services.mr.create(
    node_id=312,
    image="ubuntu:24.04",
    disk_size=20,  # GB
    http_ports=[8888],
    ports=[22],
    envs={"APP_ENV": "production"},
    start_command="python3 -m http.server 8888",
)
uuid = response.data["uuid"]
```

`node_id`, `image` and `disk_size` are required. To run an application from
**Marketplace → Applications**, pass its UUID as `app` (see
[Applications](#applications)). `http_ports` are exposed as HTTPS links,
`ports` as TCP/UDP ports.

The session is created at once; its container is still being set up. Check
`is_ready` with [`info()`](#session-details). A rejected request, for example
for an insufficient balance, raises `octaspace.APIError` with status 400 and
the reason as its message.

## VPN

Rent a VPN gateway. In the dashboard: **Marketplace → VPN**.

### List gateways

```python
for gateway in client.services.vpn.list().data:
    print(gateway["node_id"], gateway["country"], gateway["residential"])
```

### Start a session

```python
response = client.services.vpn.create(node_id=312, subkind="wg")
uuid = response.data["uuid"]
```

`subkind` is the VPN protocol, `wg` (WireGuard) by default. The
configuration to import into your VPN client is in `vpn_config` of
[`info()`](#session-details).

## Render

Rent a render node. In the dashboard: **Render → Launch Nodes**.

### List render nodes

```python
for node in client.services.render.list().data:
    print(node["node_id"], node["city"], node["blender_optix_score"])
```

### Start a session

```python
response = client.services.render.create(node_id=312, disk_size=100)
uuid = response.data["uuid"]
```

`create()` sends its keyword arguments as the request body. To start a
dedicated render worker for each GPU, pass the field by its API name:
`client.services.render.create(node_id=312, disk_size=100, **{"multi-gpu-worker": True})`.

## Sessions

Your sessions of every kind. In the dashboard: **Marketplace → Sessions**.

### List sessions

```python
for session in client.sessions.list().data:
    print(session["uuid"], session["service"], session["app_name"])

finished = client.sessions.list(recent=True).data
```

Without arguments, `list()` returns the active sessions; `recent=True` returns
the recent ones.

### Session details

```python
session = client.services.session("96e33710-ec12-11ed-8588-fa163e49e8aa")
info = session.info().data
if info["is_ready"]:
    print(info["urls"], info["ssh_direct"])
```

The fields depend on the kind of session: links to exposed HTTP ports
(`urls`), SSH access (`ssh_direct`, `ssh_proxy`, `ssh_web`), the VPN
configuration (`vpn_config`), the amount charged so far (`charge_amount`, in
Wei), traffic and duration. An unknown session raises `NotFoundError`.

### Logs

```python
logs = session.logs().data
print(logs["container"])
```

`container` holds the container output, `system` the platform's events for
the session.

### Stop

```python
session.stop(score=5)
```

`score` is your optional rating of the session, an integer. Stopping ends the
session and its charges.

## Applications

Ready-made images with their ports and settings. In the dashboard:
**Marketplace → Applications**.

```python
for app in client.apps.list().data:
    print(app["uuid"], app["name"], app["category"], app["image"])
```

Also works without an API token. Pass an application's `uuid` and `image` to
[`services.mr.create()`](#start-a-session).

## Nodes

The nodes you host. In the dashboard: **Hosting → Nodes**.

### List and get

```python
nodes = client.nodes.list().data
node = client.nodes.find(312).data
print(node["state"], node["os_version"], node["location"])
```

`find()` of a node that is not yours or does not exist raises
`NotFoundError`.

### Ident and logs

```python
ident = client.nodes.download_ident(312).body
logs = client.nodes.download_logs(312).body
```

The node's identity file and its logs. Use `.body` (bytes) when the response
is not JSON.

### Set prices

```python
client.nodes.update_prices(312, base=25, storage=2, traffic=1)
```

Pass one or more of `base`, `storage` and `traffic`, each an integer from 0
to 10000; see `node_prices` in the
[API reference](https://api.octa.space/api-docs) for the units. Any other
field or value raises `APIError` with status 400.

### Reboot

```python
client.nodes.reboot(312)
```

## Idle jobs

The jobs your nodes run while nobody rents them. In the dashboard:
**Hosting → Idle Jobs**.

```python
job = client.idle_jobs.find(node_id=312, job_id=42).data
logs = client.idle_jobs.logs(node_id=312, job_id=42).data
```

## Accounts

In the dashboard: **Account → Profile** and **Account → Billing**.

### Profile

```python
profile = client.accounts.profile().data
print(profile["email"], profile["wallet"])
```

### Balance

```python
balance = client.accounts.balance().data["balance"]
print(f"{balance / 10**18:.6f} OCTA")
```

The balance is an integer in Wei. Use `decimal.Decimal(balance) / 10**18` when
you need an exact amount.

### Generate a deposit wallet

```python
address = client.accounts.generate_wallet().data["address"]
```

Creates the deposit wallet address of your account.

## Network

Statistics of the OctaSpace network and its GPU market. Works without an API
token.

```python
network = client.network.info().data
print(network["market_price"])
for model, stats in network["marketplace"]["gpus"].items():
    print(model, stats["count"], stats["avg_price"])
```
