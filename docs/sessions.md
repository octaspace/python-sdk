# Sessions

[← Back to README](../README.md)

**On this page:** [Lifecycle](#lifecycle) · [List and get](#list-and-get) ·
[Wait until ready](#wait-until-ready) · [Connect](#connect) · [Logs](#logs) ·
[Stop](#stop) · [Session fields](#session-fields)

`client.sessions` works with your running sessions: compute, render and VPN.
`service` tells them apart; narrow a session with `is_compute_session()`,
`is_render_session()` or `is_vpn_session()`. The examples assume a client
created as in the [Quick start](../README.md#quick-start).

## Lifecycle

```text
compute.start / render.start / vpn.start ──► starting ──► ready ──► sessions.stop
                                                ▲           │
                                                └─ restart ─┘
```

| `status` | Meaning |
| --- | --- |
| `starting` | The container is being set up; see `progress` and `pull_percent` |
| `ready` | The session is running and can be used |

A stopped session is no longer returned by the API.

## List and get

```python
from octaspace import NotFoundError, is_compute_session

for s in client.sessions.list():  # running sessions, oldest first
    if is_compute_session(s):
        print(s["uuid"], s["status"], s.get("node_number"), s.get("urls"))

try:
    session = client.sessions.get(uuid)
except NotFoundError:
    ...  # the session has stopped, or the UUID is unknown
```

## Wait until ready

`wait_ready` polls a session until it is ready and returns it:

```python
from octaspace import SessionStoppedError

try:
    session = client.sessions.wait_ready(
        uuid,
        timeout=600,
        on_progress=lambda s: print(s["status"], s.get("progress"), s.get("pull_percent")),
    )
except SessionStoppedError:
    ...  # the session stopped while starting, for example because SSH could not be set up
```

| Argument | Default | Effect |
| --- | --- | --- |
| `interval` | `3.0` | Seconds between checks; keep it at 2 or more to stay within the rate limit |
| `timeout` | none | Raises a `WaitTimeoutError` (a `TimeoutError`) after this many seconds |
| `on_progress` | none | Called with the session after each check |

After `compute.restart()` the session can still report `ready` for a moment. To
see the restart finish, wait until its status leaves `ready` first.

## Connect

When a compute session is ready, these fields tell you how to reach it:

| Field | Contains |
| --- | --- |
| `ssh["direct"]`, `ssh["proxy"]` | SSH endpoints: `host`, `port` and the `user` to log in as |
| `ssh["web"]` | URL of the web terminal |
| `fm` | URL of the web file manager |
| `ports` | Each exposed container port mapped to its public port on the node |
| `urls` | Each HTTP port mapped to its public URL |

The SSH fields are `None` unless SSH was turned on when the session started,
and `fm` is `None` unless the file manager was. `ssh["direct"]` is set only when
your account has an SSH key.

> [!WARNING]
> The `ssh["web"]` URL contains credentials, and the file manager has no login.
> Do not log these URLs or show them in shared output.

`user` comes from the image's `USER`, so the image author controls it. Validate
`user` and `host`, and pass them to `ssh` as separate arguments after `--`:

```python
import subprocess

from octaspace import is_compute_session

ssh = session.get("ssh") if is_compute_session(session) else None
endpoint = ssh["proxy"] if ssh else None
if endpoint:
    host, port, user = endpoint["host"], str(endpoint["port"]), endpoint["user"]
    subprocess.run(["ssh", "-p", port, "-l", user, "--", host])
```

## Logs

```python
from datetime import UTC, datetime

logs = client.sessions.logs(uuid, tail=100)
if logs["container"] is not None:
    print(logs["container"])
for event in logs["system"]:
    ts = event.get("ts")
    print(datetime.fromtimestamp(ts / 1000, UTC) if ts else "", event["msg"])
```

| Field | Contains |
| --- | --- |
| `container` | The latest container output; `tail` sets the number of lines, 1 – 1000 (200 by default). `None` when the node cannot be reached or there is no output yet. |
| `container_truncated` | `True` if the output was cut to its last 1 MiB |
| `system` | Platform events of the session, oldest first |

Logs are available for running compute sessions. For a render or VPN session
`logs` raises a `NotFoundError`, although the session is running.

## Stop

```python
client.sessions.stop(uuid)
client.sessions.wait_stopped(uuid)
```

Stopping takes a few seconds, during which `get` can still return the session;
after that it raises a `NotFoundError`. `wait_stopped` returns once the session
is gone and takes the same `interval` and `timeout` arguments as `wait_ready`.
Stopping a session twice is safe.

> [!NOTE]
> A session stopped before its minimum rent (`min_rent_minutes`) is charged as
> if it ran that long.

## Session fields

| Field | Meaning |
| --- | --- |
| `base_price`, `storage_price`, `traffic_price` | Prices in micro-USD, fixed when the session starts |
| `charge_amount` | What the session has cost so far, in micro-USD |
| `duration` | Seconds since the start |
| `started_at` | Unix milliseconds |
| `node_hw` | The node: CPU, memory, GPUs, the rented disk in GB, network speed |

While a session is starting, its prices, `started_at` and `node_hw` are `None`.
