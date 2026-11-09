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
| `ValidationError` | 400, 422 | The request was rejected: a parameter is invalid, or a session cannot be started (for example an insufficient balance) |
| `ConflictError` | 409 | The request conflicts with the current state |
| `RateLimitError` | 429 | Too many requests |
| `ServerError` | 5xx | A temporary problem on the API side |
| `BadGatewayError`, `ServiceUnavailableError`, `GatewayTimeoutError` | 502, 503, 504 | Subclasses of `ServerError` |
| `APIError` | any other | Base class of all of the above |

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
    ├── ConflictError
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
from octaspace import ValidationError

try:
    client.services.mr.create(node_id=312, image="ubuntu:24.04", disk_size=20)
except ValidationError as exc:
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

GET requests are retried automatically on connection errors, timeouts and the
statuses 408, 429, 500, 502, 503 and 504, up to `max_retries` times (default
2), with exponential backoff and a little jitter. When the response has a
`Retry-After` header, the SDK waits that long instead; when the API asks to
wait longer than `max_retry_after` (default 60 seconds), the `RateLimitError`
is raised at once. After the last attempt the error is raised.

> [!IMPORTANT]
> Starting a session (`create()`), stopping it (`stop()`), setting prices and
> generating a wallet are retried only when the connection could not be
> established, so that they cannot run twice. After a timeout or an error
> response, decide yourself whether to repeat them. `nodes.reboot()` is a GET
> request and is retried like the others.

Set the number of retries and the waits with `max_retries`, `retry_interval`,
`backoff_factor` and `max_retry_after`; see
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

Requests are spread over the hosts in turn. When a host cannot be reached, the
request is sent to the next host, and the failed host is left out for 30
seconds. A GET request also moves to the next host after a timeout. A request
that changes something (`create()`, `stop()`, setting prices) moves only when
the connection could not be established, so that it cannot run twice. An HTTP
error response, including 5xx, does not move the request to another host.
