# Errors, rate limits and retries

[← Back to README](../README.md)

**On this page:** [Error classes](#error-classes) ·
[Reading an error](#reading-an-error) · [Rate limits](#rate-limits) ·
[Retries](#retries) · [Several API hosts](#several-api-hosts)

The examples assume a client created as in the
[Quick start](../README.md#quick-start).

## Error classes

Every error the SDK raises is an `octaspace.OctaSpaceError`. An error response
from the API raises a subclass of `APIError`:

| Class | Status | Typical cause |
| --- | --- | --- |
| `ValidationError` | 400, 422 | A parameter is missing or invalid, or the request cannot be met (for example, an insufficient balance) |
| `AuthenticationError` | 401 | The API key is missing, wrong or deleted |
| `APIPermissionError` | 403 | Access denied |
| `NotFoundError` | 404 | Unknown or stopped session, unknown node |
| `ConflictError` | 409 | The session is already starting or restarting |
| `RateLimitError` | 429 | Too many requests, or the session was restarted too recently |
| `ServerError` | 5xx | A temporary problem on the API side |
| `ServiceUnavailableError` | 503 | The service is temporarily unavailable; a subclass of `ServerError`, like `BadGatewayError` (502) and `GatewayTimeoutError` (504) |

`SessionStoppedError`, a subclass of `NotFoundError`, is raised by
[`sessions.wait_ready()`](sessions.md#wait-until-ready) when the session stops
while starting; `WaitTimeoutError` (also a `TimeoutError`) when a wait passes
its `timeout`.

When the API cannot be reached at all, the error is a `NetworkError`:
`APIConnectionError` (DNS, connection or TLS failure) or `APITimeoutError`. An
invalid client option raises `ConfigurationError`, a `ValueError`. All classes
can be imported from `octaspace`.

```text
OctaSpaceError
├── ConfigurationError
├── WaitTimeoutError
├── NetworkError
│   ├── APIConnectionError
│   └── APITimeoutError
└── APIError
    ├── ValidationError
    ├── AuthenticationError
    ├── APIPermissionError
    ├── NotFoundError
    │   └── SessionStoppedError
    ├── ConflictError
    ├── RateLimitError
    └── ServerError
        ├── BadGatewayError
        ├── ServiceUnavailableError
        └── GatewayTimeoutError
```

## Reading an error

An `APIError` has the HTTP `status_code`, the API's `message`, the
`request_id`, `retry_after`, the `rate_limit` state and the full `response`:

```python
from octaspace import APIError

try:
    client.compute.start("7KQ4-M2XD-4", "ubuntu:24.04")
except APIError as exc:
    print(f"status {exc.status_code}: {exc.message} (request {exc.request_id})")
    raise
```

> [!TIP]
> Include the request ID when you contact support about a failed call.

## Rate limits

| Requests | Limit per minute |
| --- | --- |
| Without an API key | 60 per IP address |
| With an API key | 300 per account |
| Starting and restarting sessions | 10 per account |

`client.rate_limit` returns the limit, the remaining requests and the seconds
until the limit resets (`limit`, `remaining`, `reset`), as of the latest
response. A failed call carries the same in `APIError.rate_limit`.

On a `RateLimitError`, wait `retry_after` seconds before you try again:

```python
import time

from octaspace import RateLimitError

try:
    sessions = client.sessions.list()
except RateLimitError as exc:
    time.sleep(exc.retry_after or 1)
    sessions = client.sessions.list()
```

## Retries

GET requests are retried automatically on connection errors, timeouts and the
statuses 429, 502, 503 and 504, up to `max_retries` times (default 2), with
exponential backoff and a little jitter. When the response has a `Retry-After`
header, the SDK waits that long instead; when the API asks to wait longer than
`max_retry_after` (default 60 seconds), the `RateLimitError` is raised at once.

`sessions.stop()` and the maintenance mode methods are retried the same way:
repeating them is safe.

> [!IMPORTANT]
> Requests that cost money or change prices — starting and restarting
> sessions, setting prices — are retried only when the connection could not be
> established, so that they cannot run twice. After a timeout or an error
> response, decide yourself whether to repeat them.

Set the number of retries and the waits with `max_retries`, `retry_interval`,
`backoff_factor` and `max_retry_after`; see
[Client configuration](getting-started.md#options).

## Several API hosts

`base_urls` takes a list of hosts that serve the OctaSpace API, for example
`https://api.octa.space` and a proxy of your own in front of it:

```python
import os

from octaspace import OctaSpaceClient

with OctaSpaceClient(
    api_key=os.environ["OCTA_API_KEY"],
    base_urls=["https://api.octa.space", "https://octa-proxy.example.com"],
) as client:
    client.sessions.list()
```

Requests are spread over the hosts in turn. When a host cannot be reached, the
request is sent to the next host, and the failed host is left out for 30
seconds. A GET request also moves to the next host after a timeout. A request
that costs money or changes prices moves only when the connection could not be
established, so that it cannot run twice. An HTTP error response, including
5xx, does not move the request to another host.
