# Client configuration

[← Back to README](../README.md)

**On this page:** [Creating a client](#creating-a-client) ·
[Options](#options) · [Environment variables](#environment-variables) ·
[Shared client](#shared-client) · [Timeouts](#timeouts) ·
[Keep-alive connections](#keep-alive-connections) ·
[Logging and hooks](#logging-and-hooks) · [Responses](#responses)

## Creating a client

`OctaSpaceClient` takes your [API token](../README.md#authentication) as
`api_key` and optional settings as keyword arguments:

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    read_timeout=15,
    max_retries=3,
    user_agent="my-service/1.0",
)
```

The client holds open connections. Close it when you no longer need it, or use
it as a context manager, which closes it on exit:

```python
with OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"]) as client:
    client.accounts.profile()

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
try:
    client.accounts.profile()
finally:
    client.close()
```

An unknown or invalid option raises `octaspace.ConfigurationError`, a
subclass of `ValueError`.

## Options

| Option | Default | Environment variable | Effect |
| --- | --- | --- | --- |
| `api_key` | `None` | `OCTA_API_KEY` | Your API token; without it only the [calls without a key](../README.md#calls-without-an-api-key) work |
| `base_url` | `https://api.octa.space` | `OCTA_BASE_URL` | Another API host |
| `base_urls` | `None` | `OCTA_BASE_URLS` (comma-separated) | Several API hosts, see [Several API hosts](errors-and-reliability.md#several-api-hosts); overrides `base_url` |
| `open_timeout` | `10.0` | `OCTA_OPEN_TIMEOUT` | Seconds to wait for a connection |
| `read_timeout` | `30.0` | `OCTA_READ_TIMEOUT` | Seconds to wait for a response |
| `write_timeout` | `30.0` | `OCTA_WRITE_TIMEOUT` | Seconds to wait while sending a request |
| `max_retries` | `2` | `OCTA_MAX_RETRIES` | Retries of failed requests that are safe to repeat; `0` turns them off. See [Retries](errors-and-reliability.md#retries) |
| `retry_interval` / `backoff_factor` | `0.5` / `2.0` | `OCTA_RETRY_INTERVAL` / `OCTA_BACKOFF_FACTOR` | Backoff between retries: `retry_interval × backoff_factor^attempt` seconds |
| `max_retry_after` | `60.0` | `OCTA_MAX_RETRY_AFTER` | Longest `Retry-After` the SDK waits for; a longer wait raises the error at once |
| `keep_alive` | `False` | `OCTA_KEEP_ALIVE` | Reuse connections, see [below](#keep-alive-connections) |
| `pool_size` | `5` | `OCTA_POOL_SIZE` | Connections kept open with `keep_alive` |
| `max_connections` | `20` | `OCTA_MAX_CONNECTIONS` | Most connections open at the same time |
| `pool_timeout` | `5.0` | `OCTA_POOL_TIMEOUT` | Seconds to wait for a free connection |
| `idle_timeout` | `60.0` | `OCTA_IDLE_TIMEOUT` | Seconds an unused connection stays open with `keep_alive` |
| `ssl_verify` | `True` | `OCTA_SSL_VERIFY` | Verify the server's TLS certificate |
| `user_agent` | `octaspace-python/<version>` | `OCTA_USER_AGENT` | Value of the `User-Agent` header |
| `logger` | `None` | `OCTA_LOGGER` (logger name) | A `logging.Logger`, see [below](#logging-and-hooks) |
| `on_request` / `on_response` | `None` | — | Callables run before each request and after each response |

Timeouts and intervals are in seconds.

## Environment variables

`OctaSpaceClient` does not read the environment by itself. To configure a
client from the variables in the table above, build a `ClientConfig` with
`from_env()`:

```python
from octaspace import ClientConfig, OctaSpaceClient

config = ClientConfig.from_env()
with OctaSpaceClient(config=config) as client:
    client.accounts.balance()
```

Keyword arguments to `from_env()` override the environment:
`ClientConfig.from_env(max_retries=0)`. Boolean variables accept `1`, `true`,
`yes` and `on`. An invalid number raises `ConfigurationError`.

## Shared client

To set options once for the whole process, call `octaspace.configure()`.
`octaspace.client()` without arguments returns one shared client built from
that configuration and creates it on first use:

```python
import os

import octaspace

octaspace.configure(api_key=os.environ["OCTA_API_KEY"], keep_alive=True)

octaspace.client().accounts.balance()
```

Calling `configure()` again closes the shared client; the next
`octaspace.client()` call creates a new one with the new options. Close it when
your process or worker stops:

```python
octaspace.shutdown_shared_client()
```

`octaspace.client(api_key=..., **options)` with arguments returns a new client
based on the global configuration instead of the shared one. You own that
client: close it yourself.

```python
with octaspace.client(api_key=os.environ["OCTA_API_KEY"]) as user_client:
    user_client.accounts.profile()
```

`octaspace.reset_configuration()` closes the shared client and restores the
defaults.

## Timeouts

The timeouts apply to each attempt of a request. A request that is retried can
take longer in total; set `max_retries=0` if you need a hard limit.

A request that takes too long raises `octaspace.APITimeoutError`.

## Keep-alive connections

By default, every request opens a new connection and sends
`Connection: close`. With `keep_alive=True` the client keeps up to `pool_size`
connections open and reuses them, which saves a TLS handshake per request:

```python
with OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    keep_alive=True,
    pool_size=10,
    idle_timeout=120,
) as client:
    print(client.transport_stats())
```

`transport_stats()` returns the connection mode, the pool limits and the API
host in use:

```python
{
    "mode": "persistent",
    "limits": {"max_keepalive_connections": 10, "max_connections": 20, "keepalive_expiry": 120},
    "url": "https://api.octa.space",
}
```

## Logging and hooks

Pass a `logging.Logger` as `logger`. The SDK logs the method and URL of each
request at `DEBUG` level:

```text
octaspace -> GET https://api.octa.space/accounts/balance
```

> [!NOTE]
> The API token, other headers and request and response bodies are never
> logged.

`on_request` receives a `RequestContext` with `method` (lower case), `path` and
`params`; `on_response` receives the `APIResponse`. Use them for metrics or
tracing:

```python
from octaspace import OctaSpaceClient
from octaspace.hooks import RequestContext
from octaspace.response import APIResponse


def on_request(ctx: RequestContext) -> None:
    print("->", ctx.method.upper(), ctx.path)


def on_response(response: APIResponse) -> None:
    print("<-", response.status_code)


client = OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    on_request=on_request,
    on_response=on_response,
)
```

An exception raised in a hook propagates to the caller of the SDK method.

## Responses

Every resource method returns an `octaspace.response.APIResponse`:

| Attribute | Meaning |
| --- | --- |
| `data` | The parsed JSON body, or `None` if the body is empty or not JSON |
| `body` | The raw body as `bytes` |
| `status_code` | HTTP status |
| `headers` | Response headers |
| `request_id` | Value of the `X-Request-Id` header, or `None` |

The fields of each response are described in the
[OctaSpace API reference](https://api.octa.space/api-docs).
