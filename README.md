# octaspace

Official Python SDK for the [OctaSpace API](https://api.octa.space/api-docs).

## Features

- Resource-oriented API: `client.nodes.list()`, `client.services.session(uuid).stop()`
- Sync-first client built on `httpx`
- Keep-alive mode with configurable pool limits
- URL rotation / failover across multiple base URLs
- Retry with exponential backoff and `Retry-After` handling
- Typed error hierarchy with request ID and raw response access
- `on_request` / `on_response` hooks for logging, tracing, and diagnostics
- Shared client helpers for application-style integrations
- Browser playground for manual QA against mock scenarios or the live API
- Typed models for `Account`, `Balance`, `Node`, and `Session`

## Installation

### From PyPI

Use this after the first public PyPI release. Until then, use the local development setup below.

```bash
pip install octaspace
```

If you use `uv`:

```bash
uv add octaspace
```

### Local Development Setup

Recommended modern setup from the repository root:

```bash
uv sync --group dev
```

This installs the SDK in editable mode together with test, lint, typecheck, and playground dependencies.

If you prefer a plain virtualenv + `pip` flow:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . pytest pytest-cov respx mypy ruff hatchling fastapi jinja2 python-multipart uvicorn
```

## Quick Start

```python
from octaspace import OctaSpaceClient

# Public endpoint
with OctaSpaceClient() as client:
    print(client.network.info().data)

# Authenticated endpoints
with OctaSpaceClient(api_key="your-api-key") as client:
    print(client.accounts.profile().data)
    print(client.accounts.balance().data)
    print(client.nodes.list().data)
```

### Resource Examples

```python
from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key="your-api-key")

# Accounts
client.accounts.profile()                # GET /accounts
client.accounts.balance()                # GET /accounts/balance
client.accounts.generate_wallet()        # POST /accounts

# Nodes
client.nodes.list()                      # GET /nodes
client.nodes.find(123)                   # GET /nodes/:id
client.nodes.download_ident(123)         # GET /nodes/:id/ident
client.nodes.download_logs(123)          # GET /nodes/:id/logs
client.nodes.update_prices(123, gpu_hour=0.5)  # PATCH /nodes/:id/prices
client.nodes.reboot(123)                 # GET /nodes/:id/reboot

# Sessions
client.sessions.list()                   # GET /sessions
client.sessions.list(recent=True)        # GET /sessions?recent=true

# Session proxy
session = client.services.session("uuid-here")
session.info()                           # GET /services/:uuid/info
session.logs()                           # GET /services/:uuid/logs
session.stop(score=5)                    # POST /services/:uuid/stop

# Services
client.services.mr.list()                # GET /services/mr
client.services.mr.create(
    node_id=1,
    disk_size=10,
    image="ubuntu:24.04",
    app="249b4cb3-3db1-4c06-98a4-772ba88cd81c",
)                                        # POST /services/mr

client.services.vpn.list()               # GET /services/vpn
client.services.vpn.create(node_id=1, subkind="wg")  # POST /services/vpn

client.services.render.list()            # GET /services/render
client.services.render.create(node_id=1, disk_size=100)  # POST /services/render

# Apps
client.apps.list()                       # GET /apps

# Network
client.network.info()                    # GET /network

# Idle Jobs
client.idle_jobs.find(node_id=69, job_id=42)  # GET /idle_jobs/:node_id/:job_id
client.idle_jobs.logs(node_id=69, job_id=42)  # GET /idle_jobs/:node_id/:job_id/logs

client.close()
```

## Shared Client And App Integration

Like the Ruby SDK, the Python package exposes a process-level shared client for app-style integrations.

### Global configuration

```python
import octaspace

octaspace.configure(
    api_key="your-api-key",
    keep_alive=True,
    pool_size=10,
)
```

### Shared client

`octaspace.client()` with no arguments returns a lazily initialized shared client based on the current global configuration:

```python
import octaspace

octa_client = octaspace.client()
print(octa_client.network.info().data)
```

Pass arguments to create a one-off client instead:

```python
import octaspace

user_client = octaspace.client(api_key="per-user-token")
print(user_client.accounts.profile().data)
user_client.close()
```

### Shutdown

When your process stops, or when a worker is recycling, close the shared client explicitly:

```python
import octaspace

octaspace.shutdown_shared_client()
```

You can also reset the global configuration:

```python
import octaspace

octaspace.reset_configuration()
```

## Configuration Reference

| Option | Default | Description |
| --- | --- | --- |
| `api_key` | `None` | API key sent as the `Authorization` header |
| `base_url` | `https://api.octa.space` | Primary API endpoint |
| `base_urls` | `None` | Multiple endpoints enabling rotation / failover |
| `keep_alive` | `False` | Reuse pooled connections instead of forcing `Connection: close` |
| `pool_size` | `5` | Maximum keep-alive connections |
| `max_connections` | `20` | Total connection cap |
| `pool_timeout` | `5.0` | Seconds to wait for an available pooled connection |
| `idle_timeout` | `60.0` | Keep-alive expiry in seconds |
| `open_timeout` | `10.0` | TCP connect timeout |
| `read_timeout` | `30.0` | Response read timeout |
| `write_timeout` | `30.0` | Request body write timeout |
| `max_retries` | `2` | Retry attempts on retryable responses |
| `retry_interval` | `0.5` | Base retry interval in seconds |
| `backoff_factor` | `2.0` | Exponential backoff multiplier |
| `ssl_verify` | `True` | Toggle TLS certificate verification |
| `on_request` | `None` | Callable receiving `RequestContext` before each request |
| `on_response` | `None` | Callable receiving `APIResponse` after each response |
| `logger` | `None` | Standard-library logger used by hook dispatch |
| `user_agent` | auto | Override the default SDK user agent |

### Environment Loading

`ClientConfig.from_env()` reads configuration from environment variables:

```python
from octaspace.config import ClientConfig

config = ClientConfig.from_env()
```

Supported variables:

- `OCTA_API_KEY`
- `OCTA_BASE_URL`
- `OCTA_BASE_URLS`
- `OCTA_KEEP_ALIVE`
- `OCTA_POOL_SIZE`
- `OCTA_MAX_CONNECTIONS`
- `OCTA_POOL_TIMEOUT`
- `OCTA_IDLE_TIMEOUT`
- `OCTA_OPEN_TIMEOUT`
- `OCTA_READ_TIMEOUT`
- `OCTA_WRITE_TIMEOUT`
- `OCTA_MAX_RETRIES`
- `OCTA_RETRY_INTERVAL`
- `OCTA_BACKOFF_FACTOR`
- `OCTA_SSL_VERIFY`
- `OCTA_LOGGER`
- `OCTA_USER_AGENT`

`OCTA_BASE_URLS` accepts a comma-separated list.

## Keep-Alive Mode

```python
from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key="your-api-key",
    keep_alive=True,
    pool_size=10,
    idle_timeout=120,
) as client:
    print(client.transport_stats())
```

Example transport stats:

```python
{
    "mode": "persistent",
    "limits": {
        "max_keepalive_connections": 10,
        "max_connections": 20,
        "keepalive_expiry": 120.0,
    },
    "url": "https://api.octa.space",
}
```

## URL Rotation / Failover

```python
from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key="your-api-key",
    base_urls=[
        "https://api.octa.space",
        "https://api.octa.computer",
    ],
) as client:
    print(client.transport_stats())
```

Behaviour:

- healthy endpoints are selected round-robin
- connection and timeout failures temporarily mark a URL as failed
- failed URLs automatically re-enter rotation after cooldown
- if only one URL is configured, no rotator is created

## Hooks

```python
import logging

from octaspace import OctaSpaceClient

logger = logging.getLogger("octaspace-demo")

def on_request(ctx) -> None:
    logger.info("-> %s %s", ctx.method.upper(), ctx.path)

def on_response(response) -> None:
    logger.info("<- %s %s", response.status_code, response.request_id)

with OctaSpaceClient(
    api_key="your-api-key",
    on_request=on_request,
    on_response=on_response,
    logger=logger,
) as client:
    client.network.info()
```

## Error Handling

```python
from octaspace import (
    APIConnectionError,
    APIPermissionError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OctaSpaceClient,
    RateLimitError,
    ValidationError,
)

try:
    with OctaSpaceClient(api_key="token") as client:
        client.nodes.find(999_999)
except NotFoundError as exc:
    print("Not found", exc.request_id)
except AuthenticationError:
    print("Invalid API key")
except APIPermissionError:
    print("Permission denied")
except ValidationError as exc:
    print("Validation failed", exc)
except RateLimitError as exc:
    print("Retry after", exc.retry_after)
except (APIConnectionError, APITimeoutError) as exc:
    print("Network issue", exc)
```

### Error Hierarchy

```text
OctaSpaceError
├── ConfigurationError
├── NetworkError
│   ├── APIConnectionError
│   └── APITimeoutError
└── APIError
    ├── AuthenticationError        401
    ├── APIPermissionError         403
    ├── NotFoundError              404
    ├── ValidationError            422
    ├── RateLimitError             429
    └── ServerError                5xx
        ├── BadGatewayError        502
        ├── ServiceUnavailableError 503
        └── GatewayTimeoutError    504
```

All `APIError` subclasses expose:

- `status_code`
- `request_id`
- `response`

`RateLimitError` also exposes `retry_after`.

## Typed Models

Resources return `APIResponse` objects by default. If you want structured helper objects, use the typed models explicitly:

```python
from octaspace import OctaSpaceClient
from octaspace.models import Node

with OctaSpaceClient(api_key="your-api-key") as client:
    response = client.nodes.find(123)
    node = Node.from_dict(response.data)
    print(node.id)
    print(node.state)
    print(node.online)
```

Available models: `Node`, `Account`, `Balance`, `Session`.

## Browser Playground

The repository includes a development-only FastAPI playground. It is **not included in the published PyPI wheel** and exists for manual SDK QA, mirroring the role of the Ruby dummy app.

### Start

From the repository root:

```bash
uv sync --group playground
uvicorn playground.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/playground/dashboard
```

### What The Playground Covers

- the same page set and general layout direction as the Ruby dummy app
- sidebar runtime settings for API key, transport scenario, and base URL
- direct pages for dashboard, network, account, apps, nodes, sessions, services, idle jobs, and diagnostics
- footer request log for every SDK call triggered through the playground
- deterministic offline QA via the `Fixtures` scenario
- failure simulation via `401`, `403`, `404`, `429`, `500`, `slow`, `timeout`, and `network-error`
- live QA against the real API when `Transport = Real API`

### Routes

| Route | Content |
| --- | --- |
| `/playground/dashboard` | Network + account summary |
| `/playground/network` | Public network endpoint and transport summary |
| `/playground/account` | Profile + balance view |
| `/playground/apps` | App catalog |
| `/playground/nodes` | Node list + detail panel |
| `/playground/nodes/{id}` | Standalone node detail |
| `/playground/sessions` | Current and recent sessions |
| `/playground/services` | Machine Rental, Render, and VPN tabs |
| `/playground/idle-jobs` | Idle job details + logs |
| `/playground/diagnostics` | Direct SDK call execution + smoke suite |

Notes:

- the sidebar intentionally mirrors the Ruby dummy app navigation, so `Account` exists as a direct route but is not shown in the nav
- request log lives in the footer, not on a separate `Requests` page
- diagnostics includes mutation methods; only run them against disposable targets when using real credentials

Detailed QA steps live in:

- [`docs/runbooks/browser-playground.md`](docs/runbooks/browser-playground.md)
- [`docs/runbooks/console-verification.md`](docs/runbooks/console-verification.md)

## Repository Smoke Command

The repository exposes both a module entry point and a script entry point:

```bash
.venv/bin/python -m octaspace
.venv/bin/octaspace-smoke
```

If `OCTA_API_KEY` is present, smoke output includes `accounts.balance()` as well as `network.info()`.

## Console And REPL Usage

### Quick REPL Session

```bash
.venv/bin/python
```

```python
>>> from octaspace import OctaSpaceClient
>>> client = OctaSpaceClient()
>>> client.network.info().data
>>> client.close()
```

### Authenticated REPL Session

```bash
read -s OCTA_API_KEY
export OCTA_API_KEY
.venv/bin/python
```

`read -s OCTA_API_KEY` and `export OCTA_API_KEY` are shell commands, not Python statements. Run them in `zsh` / `bash`, type the token when prompted, press `Enter`, and only then start Python.

```python
>>> import os
>>> from octaspace import OctaSpaceClient
>>> client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"], keep_alive=True, pool_size=10)
>>> client.accounts.profile().data
>>> client.accounts.balance().data
>>> len(client.nodes.list().data)
>>> len(client.sessions.list().data)
>>> client.transport_stats()
>>> client.close()
```

If you are already inside Python REPL, set the variable there instead of using `read`:

```python
>>> import os, getpass
>>> os.environ["OCTA_API_KEY"] = getpass.getpass("OCTA_API_KEY: ")
```

### Local Mock Console Script

```bash
.venv/bin/python examples/console_mock.py
```

Expected output includes:

- `transport_stats`
- `network`
- `profile`
- `balance`
- `nodes`
- `session_info`
- `session_stop`

### Local Real Console Script

```bash
.venv/bin/python examples/console_real.py
```

Optional environment variables:

- `OCTA_API_KEY`
- `OCTA_SESSION_UUID`
- `OCTA_ALLOW_STOP=1`

If `OCTA_API_KEY` is unset, the script still verifies the public network endpoint and skips authenticated checks explicitly.

## Development

### Local Checks

```bash
.venv/bin/ruff check src tests examples playground
.venv/bin/mypy src/octaspace playground
.venv/bin/pytest
```

Or with `uv` if installed:

```bash
uv run ruff check src tests examples playground
uv run mypy src/octaspace playground
uv run pytest
```

### Build And Wheel Smoke Test

Build the distribution:

```bash
.venv/bin/python -m build
```

Or with `uv`:

```bash
uv build
```

Inspect the wheel contents (should only contain `octaspace/`, no `playground/`):

```bash
python3 -m zipfile -l dist/octaspace-*.whl | grep -v dist-info
```

Create a clean environment and install the built wheel:

```bash
python3 -m venv /tmp/octaspace-wheel-test
/tmp/octaspace-wheel-test/bin/python -m pip install dist/octaspace-*.whl
/tmp/octaspace-wheel-test/bin/python -c "from octaspace import OctaSpaceClient; print(OctaSpaceClient().network.info().data)"
```

### Verification Runbooks

- [`docs/runbooks/console-verification.md`](docs/runbooks/console-verification.md)
- [`docs/runbooks/browser-playground.md`](docs/runbooks/browser-playground.md)
- [`docs/runbooks/publish.md`](docs/runbooks/publish.md)

Release gate:

1. `ruff` clean
2. `mypy` clean
3. `pytest` all passing
4. console verification completed
5. browser playground verification completed
6. wheel smoke test passing
7. follow `docs/runbooks/publish.md` for TestPyPI → PyPI

## License

[MIT](LICENSE)
