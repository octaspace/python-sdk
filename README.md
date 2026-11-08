# OctaSpace Python SDK

[![PyPI](https://img.shields.io/pypi/v/octaspace)](https://pypi.org/project/octaspace/)
[![Python](https://img.shields.io/pypi/pyversions/octaspace)](https://pypi.org/project/octaspace/)
[![CI](https://github.com/octaspace/python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/octaspace/python-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/octaspace/python-sdk/blob/main/LICENSE)

The official Python library for the [OctaSpace](https://octa.space) API. Rent
machines, VPN gateways and render nodes, manage your sessions and the nodes you
host, and read network statistics from Python code.

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

1. [Copy your API token](#authentication) and export it:

   ```bash
   export OCTA_API_KEY="your-api-token"
   ```

2. Run this program:

   ```python
   import os

   from octaspace import AuthenticationError, OctaSpaceClient

   with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"]) as client:
       try:
           balance = client.accounts.balance().data["balance"]
           print(f"Balance: {balance / 10**18:.6f} OCTA")

           for machine in client.services.mr.list().data:
               gpus = ", ".join(gpu["model"] for gpu in machine.get("gpus", []))
               print(machine["node_id"], machine["country"], gpus or "no GPU")
       except AuthenticationError:
           raise SystemExit("The API token is missing, wrong or regenerated.") from None
   ```

Every method returns an `APIResponse`; the parsed JSON is in `.data`. Create
one client, reuse it, and close it when you are done (the `with` block does
that for you).

## Authentication

The SDK authenticates with the **API token** of your OctaSpace account. You
find it in the OctaSpace dashboard:

1. Sign in to the [OctaSpace dashboard](https://cube.octa.space).
2. In the sidebar, open **Account → Credentials**.
3. Copy the value of the **API Token** field.

Your account has one API token. It authenticates API requests to manage your
account programmatically.

Pass the token as `api_key`. The SDK sends it in the `Authorization: <token>`
header.

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
```

> **Important:** Regenerating the token (the refresh button next to
> **API Token**) invalidates the previous one at once, for every program that
> uses it. Update the token everywhere after you regenerate it.

> **Warning:** The API token acts on behalf of your account: it can start
> sessions that are charged to your balance. Keep it out of source code and
> version control. If it leaks, regenerate it under **Account → Credentials**.

### Calls without an API key

These methods also work without a token. Create the client without `api_key`
to use them anonymously:

| Method | Without a token |
| --- | --- |
| `network.info()` | Works |
| `apps.list()` | Works |
| `services.mr.list()` | Works |

Every other method needs a token. Without one, the API rejects the call,
usually with `AuthenticationError`.

## Handling errors

Every error the SDK raises is an `octaspace.OctaSpaceError`. Catch the specific
class you can handle:

```python
from octaspace import APIError, AuthenticationError, NotFoundError, RateLimitError

try:
    client.services.session("96e33710-ec12-11ed-8588-fa163e49e8aa").info()
except AuthenticationError:
    ...  # the API token is missing, wrong or regenerated
except NotFoundError:
    ...  # unknown session
except RateLimitError as exc:
    ...  # too many requests; wait exc.retry_after seconds
except APIError as exc:
    print(exc.status_code, exc)  # any other error response, with the API's message
```

See [Errors and reliability](https://github.com/octaspace/python-sdk/blob/main/docs/errors-and-reliability.md).

## API overview

| Resource | Dashboard section | Operations | Guide |
| --- | --- | --- | --- |
| `client.services.mr` | Marketplace → Compute | List machines, start a session | [Machine rental](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#machine-rental) |
| `client.services.vpn` | Marketplace → VPN | List gateways, start a session | [VPN](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#vpn) |
| `client.services.render` | Render → Launch Nodes | List render nodes, start a session | [Render](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#render) |
| `client.sessions`, `client.services.session(uuid)` | Marketplace → Sessions | List, info, logs, stop | [Sessions](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#sessions) |
| `client.apps` | Marketplace → Applications | List applications | [Applications](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#applications) |
| `client.nodes` | Hosting → Nodes | Your nodes, ident, logs, prices, reboot | [Nodes](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#nodes) |
| `client.idle_jobs` | Hosting → Idle Jobs | Job details and logs | [Idle jobs](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#idle-jobs) |
| `client.accounts` | Account → Profile, Account → Billing | Profile, balance, deposit wallet | [Accounts](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#accounts) |
| `client.network` | — | Network and market statistics | [Network](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md#network) |

The fields of every response are described in the
[OctaSpace API reference](https://api.octa.space/api-docs).

## Documentation

| Guide | Covers |
| --- | --- |
| [Client configuration](https://github.com/octaspace/python-sdk/blob/main/docs/getting-started.md) | Options and defaults, environment variables, shared client, keep-alive, hooks and logging |
| [Resources](https://github.com/octaspace/python-sdk/blob/main/docs/resources.md) | Every method, with an example |
| [Errors and reliability](https://github.com/octaspace/python-sdk/blob/main/docs/errors-and-reliability.md) | Error classes, retries, several API hosts |
| [Changelog](https://github.com/octaspace/python-sdk/blob/main/CHANGELOG.md) | Changes in each release |

## Versioning

The library follows [Semantic Versioning](https://semver.org). Until version
1.0, a minor release can contain breaking changes; the
[changelog](https://github.com/octaspace/python-sdk/blob/main/CHANGELOG.md)
marks them as **Breaking**.

## License

[MIT](https://github.com/octaspace/python-sdk/blob/main/LICENSE)
