# OctaSpace Python SDK

[![PyPI](https://img.shields.io/pypi/v/octaspace)](https://pypi.org/project/octaspace/)
[![Python](https://img.shields.io/pypi/pyversions/octaspace)](https://pypi.org/project/octaspace/)
[![CI](https://github.com/octaspace/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/octaspace/python-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/octaspace/python-sdk/blob/main/LICENSE)

The official Python library for the [OctaSpace](https://octa.space) API. Rent
compute machines, render nodes and VPN, manage sessions and the nodes you host,
and read GPU market statistics from Python code.

**Contents:** [Installation](#installation) · [Quick start](#quick-start) ·
[Authentication](#authentication) · [Handling errors](#handling-errors) ·
[API overview](#api-overview) · [Documentation](#documentation) ·
[Versioning](#versioning) · [License](#license)

## Installation

```bash
pip install octaspace
```

or, with [uv](https://docs.astral.sh/uv/):

```bash
uv add octaspace
```

Requires Python 3.11 or later. The only runtime dependency is
[httpx](https://www.python-httpx.org/).

## Quick start

1. [Create an API key](#authentication) and export it:

   ```bash
   export OCTA_API_KEY="octa_ak_..."
   ```

2. Save this program as `quickstart.py` and run it with `python quickstart.py`:

   ```python
   import os

   from octaspace import APIError, OctaSpaceClient, format_usd

   with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"]) as client:
       try:
           balance = client.accounts.balance()
           print("Balance:", format_usd(balance["balance"]))  # Balance: $12.500000

           for machine in client.compute.list():
               price = format_usd(machine["base_price"])
               print(machine["node_number"], machine["city"], price, "per hour")
       except APIError as exc:
           raise SystemExit(f"{exc.status_code}: {exc}") from None
   ```

Methods return the API's JSON as plain `dict` and `list` objects, typed for
your editor and type checker. Create one client, reuse it, and close it when you
are done (the `with` block does that for you).

## Authentication

The SDK authenticates with an **API key** of your OctaSpace account. You create
and delete API keys in the OctaSpace dashboard:

1. Sign in to the [OctaSpace dashboard](https://console.octa.space).
2. In the sidebar, open **Account → Credentials**.
3. In the **API Keys** section, click **New key**.
4. Enter a **Label** that tells you where the key is used, for example
   `billing-service`, and click **Create key**.
5. Copy the key. It starts with `octa_ak_`.

> **Important:** The key is shown in full only once, right after you create it.
> Copy it before you close the dialog. If you lose it, delete it and create a
> new one.

Pass the key as `api_key`, for example from the `OCTA_API_KEY` environment
variable. The SDK sends it in the `Authorization: Bearer <key>` header.

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
```

> **Warning:** An API key acts on behalf of your account: it can start sessions
> that are charged to your balance. Keep it out of source code and version
> control. If a key leaks, delete it under **Account → Credentials → API Keys**;
> every program that uses it stops working at once.

The **API Keys** list shows each key's label, its first characters and when it
was last used. Use a separate key for each program or machine, so that you can
delete one without affecting the others. The number of keys per account is
limited; the counter next to **API Keys** shows how many you have.

### Calls without an API key

These methods also work without an API key. Create the client without
`api_key` to use them anonymously:

| Method | Without a key |
| --- | --- |
| `network.info()`, `network.history()` | Same result |
| `stats.gpu_current()`, `stats.gpu_history()`, `stats.gpu_locations()`, `stats.mining()` | Same result |
| `compute.list()`, `render.list()`, `vpn.list()` | Refreshed about once an hour instead of every 10 seconds |
| `compute.apps()` | Official apps only, without your own |

Every other method requires an API key. Without one it raises an
`AuthenticationError` before the request is sent.

## Handling errors

Every error the SDK raises is an `octaspace.OctaSpaceError`. Errors returned by
the API are subclasses of `APIError`; catch the ones you can handle:

```python
from octaspace import AuthenticationError, RateLimitError, ValidationError

try:
    client.compute.start("7KQ4-M2XD-4", "ubuntu:24.04")
except AuthenticationError:
    ...  # the API key is missing, wrong or deleted
except ValidationError as exc:
    print(exc)  # the request was rejected, for example: Insufficient balance
except RateLimitError as exc:
    ...  # too many requests; wait exc.retry_after seconds
```

See [Errors, rate limits and retries](https://github.com/octaspace/python-sdk/blob/main/docs/errors-and-reliability.md).

## API overview

| Resource | Dashboard section | Operations | Guide |
| --- | --- | --- | --- |
| `client.compute` | Marketplace → Compute, Applications | List machines and apps, start, batch start, restart | [Compute](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#compute) |
| `client.render` | Render → Launch Nodes | List render nodes, start, batch start | [Render](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#render) |
| `client.vpn` | Marketplace → VPN | List VPN nodes, start | [VPN](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#vpn) |
| `client.sessions` | Marketplace → Sessions, Render → Render Nodes | List, get, logs, stop, wait until ready or stopped | [Sessions](https://github.com/octaspace/python-sdk/blob/main/docs/sessions.md) |
| `client.hosting` | Hosting → Nodes | Your nodes, one node, set prices, maintenance | [Hosting](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#hosting) |
| `client.accounts` | Account → Billing | Balance | [Accounts](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#accounts) |
| `client.network` | — | Platform statistics now and over time | [Network](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#network) |
| `client.stats` | — | GPU market: current, history, locations; mining | [Stats](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#stats) |

Every class and method has a docstring, and the package ships type hints
(`py.typed`).

## Documentation

| Guide | Covers |
| --- | --- |
| [Client configuration](https://github.com/octaspace/python-sdk/blob/main/docs/getting-started.md) | Options and defaults, environment variables, shared client, timeouts, keep-alive, hooks and logging |
| [Resources](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md) | Compute, render, VPN, hosting, balance, network and GPU statistics |
| [Sessions](https://github.com/octaspace/python-sdk/blob/main/docs/sessions.md) | Waiting until ready, connecting, logs, stopping |
| [Errors, rate limits and retries](https://github.com/octaspace/python-sdk/blob/main/docs/errors-and-reliability.md) | Error classes, limits, automatic retries, several API hosts |
| [Changelog](https://github.com/octaspace/python-sdk/blob/main/CHANGELOG.md) | Changes in each release |

## Versioning

The library follows [Semantic Versioning](https://semver.org). Until version
1.0, a minor release can contain breaking changes; the
[changelog](https://github.com/octaspace/python-sdk/blob/main/CHANGELOG.md)
marks them as **Breaking**.

## License

[MIT](https://github.com/octaspace/python-sdk/blob/main/LICENSE)
