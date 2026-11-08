# Errors and reliability

[← Back to README](../README.md)

**On this page:** [Error classes](#error-classes) ·
[Reading an error](#reading-an-error) · [Retries](#retries) ·
[Several API hosts](#several-api-hosts)

The examples assume a client created as in the
[Quick start](../README.md#quick-start):

```python
import os

from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.environ["OCTA_API_KEY"])
```

## Error classes

Every error the SDK raises is an `octaspace.OctaSpaceError`. An error response
from the API raises a subclass of `APIError`:

| Class | Status | Typical cause |
| --- | --- | --- |
| `AuthenticationError` | 401 | The API token is missing, wrong or regenerated |
| `APIPermissionError` | 403 | Access denied |
| `NotFoundError` | 404 | Unknown session, or a node that is not yours |
| `ValidationError` | 422 | A parameter is invalid |
| `RateLimitError` | 429 | Too many requests |
| `ServerError` | 5xx | A temporary problem on the API side |
| `BadGatewayError`, `ServiceUnavailableError`, `GatewayTimeoutError` | 502, 503, 504 | Subclasses of `ServerError` |
| `APIError` | any other | For example 400 when a session cannot be started (insufficient balance) or prices are invalid |

When the API cannot be reached at all, the error is a `NetworkError`:
`APIConnectionError` (DNS, connection or TLS failure) or `APITimeoutError`.
An invalid client option raises `ConfigurationError`. All classes can be
imported from `octaspace`.

```text
OctaSpaceError
├── ConfigurationError
├── NetworkError
│   ├── APIConnectionError
│   └── APITimeoutError
└── APIError
    ├── AuthenticationError
    ├── APIPermissionError
    ├── NotFoundError
    ├── ValidationError
    ├── RateLimitError
    └── ServerError
        ├── BadGatewayError
        ├── ServiceUnavailableError
        └── GatewayTimeoutError
```

## Reading an error

An `APIError` has the HTTP `status_code`, the `request_id` (or `None`) and the
full `response`. Its message is the API's reason when the response has one:

```python
from octaspace import APIError

try:
    client.services.mr.create(node_id=312, image="ubuntu:24.04", disk_size=20)
except APIError as exc:
    print(f"status {exc.status_code}: {exc}")  # status 400: Insufficient balance
    print(exc.response.data)
```

On a `RateLimitError`, `retry_after` is the number of seconds the API asks you
to wait, or `None`:

```python
import time

from octaspace import RateLimitError

try:
    sessions = client.sessions.list().data
except RateLimitError as exc:
    time.sleep(exc.retry_after or 60)
    sessions = client.sessions.list().data
```

> [!TIP]
> Include the request ID, if there is one, when you contact support about a
> failed call.

## Retries

GET requests are retried automatically on the statuses 408, 429, 500, 502,
503 and 504, up to `max_retries` times (default 2), with exponential backoff
and a little jitter. When the response has a `Retry-After` header, the SDK
waits that many seconds instead. After the last attempt the error is raised.

> [!IMPORTANT]
> Starting a session (`create()`), stopping it (`stop()`), setting prices and
> generating a wallet are never retried, so that they cannot run twice.
> Decide yourself whether to repeat them after an error. `nodes.reboot()` is a
> GET request and is retried like the others.

A connection error or a timeout is not retried on the same host. With
[several API hosts](#several-api-hosts) the request moves to the next host.

Set the number of retries and the backoff with `max_retries`,
`retry_interval` and `backoff_factor`; see
[Client configuration](getting-started.md#options).

## Several API hosts

`base_urls` takes a list of API hosts. `https://api.octa.space` and
`https://api.octa.computer` serve the same API:

```python
import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    base_urls=["https://api.octa.space", "https://api.octa.computer"],
) as client:
    client.nodes.list()
```

Requests are spread over the hosts in turn. When a host cannot be reached or
times out, the request is sent to the next host, and the failed host is left
out for 30 seconds. An HTTP error response, including 5xx, does not move the
request to another host.

> [!WARNING]
> This also applies to `create()` and `stop()`. A request that timed out may
> still have reached the API: before you start a session again, check
> `client.sessions.list()`.
