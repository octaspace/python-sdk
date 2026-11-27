# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `client.compute`: `list()`, `apps()`, `start()`, `start_batch()` and
  `restart()`. Machines are identified by their node number, such as
  `7KQ4-M2XD-4`.
- `client.render`: `list()`, `start()` and `start_batch()`.
- `client.vpn`: `list()` and `start(node_number, subkind)` for `wg`, `awg`,
  `reality` and `http_proxy`.
- `client.sessions`: `get()`, `logs(uuid, tail=)`, `stop()`, `wait_ready()`
  and `wait_stopped()`, and the helpers `is_compute_session()`,
  `is_render_session()` and `is_vpn_session()`.
- `client.hosting`: `nodes()`, `get()`, `set_prices()`,
  `start_maintenance()` and `end_maintenance()`.
- `client.network.history()` and `client.stats` (`gpu_current()`,
  `gpu_history()`, `gpu_locations()`, `mining()`), with the helpers
  `network_history_points()` and `gpu_history_points()`.
- Typed responses: `TypedDict` classes in `octaspace.types`.
- `format_usd()`, `micro_usd_to_usd()` and `usd_to_micro_usd()` for amounts
  in micro-USD.
- `client.rate_limit` and `APIError.rate_limit`; `retry_after`, `message`,
  `code` and `body` on every `APIError`.
- `SessionStoppedError` and `WaitTimeoutError`.
- `ConflictError` for HTTP 409.
- `DEFAULT_BASE_URL` and the `OCTA_API_URL` environment variable.
- The `max_retry_after` option (`OCTA_MAX_RETRY_AFTER`): the longest
  `Retry-After` the client waits for, 60 seconds by default.
- `Retry-After` given as an HTTP date.

### Changed

- **Breaking:** the client authenticates with an API key of your account
  (`octa_ak_…`, created under Account → Credentials → API Keys), sent as
  `Authorization: Bearer <key>`. Calls that need a key raise
  `AuthenticationError` before the request is sent when the client has none.
- **Breaking:** methods return the parsed JSON instead of `APIResponse`.
- **Breaking:** prices, charges and the balance are integers in micro-USD.
- **Breaking:** GET requests are retried on 429, 502, 503 and 504, no longer
  on 408 and 500.
- HTTP 400 raises `ValidationError` instead of `APIError`.
- GET, PUT and DELETE requests are retried after connection errors and
  timeouts, not only after error responses.
- `ConfigurationError` is also a `ValueError`; invalid `OCTA_*` numbers raise
  it.
- Any transport failure raises `APIConnectionError` or `APITimeoutError`
  instead of an `httpx` exception. A successful response that is not JSON
  raises `APIError`.
- **Breaking:** Python 3.11 or later is required; Python 3.10 is no longer
  supported.

### Removed

- **Breaking:** `client.services` (`mr`, `vpn`, `render`, `session(uuid)`),
  `client.nodes`, `client.apps`, `client.idle_jobs`, `accounts.profile()`,
  `accounts.generate_wallet()`, `stop(score=…)`, and the models `Account`,
  `Balance`, `Node` and `Session`. Use `client.compute`, `client.render`,
  `client.vpn`, `client.sessions` and `client.hosting`.
- **Breaking:** the `octaspace-smoke` command and `python -m octaspace`.

### Fixed

- With several API hosts, a request that changes something (starting a
  session, setting prices) is no longer sent to another host after a timeout,
  so that it cannot run twice.
- The API key no longer appears in `repr()` of `ClientConfig`.

## [0.1.0] - 2026-04-14

### Added

- `OctaSpaceClient` with the resources `accounts`, `nodes`, `sessions`,
  `apps`, `network`, `idle_jobs` and `services` (`mr`, `vpn`, `render` and
  `session(uuid)`).
- `APIResponse` with the parsed JSON, raw body, headers and request ID.
- Error classes for each HTTP status, network errors and timeouts.
- Automatic retries with exponential backoff and `Retry-After`.
- Several API hosts with failover (`base_urls`).
- Keep-alive connection pool, `on_request` / `on_response` hooks and logging.
- `ClientConfig.from_env()` and a shared client (`octaspace.configure()`,
  `octaspace.client()`).
- Models `Account`, `Balance`, `Node` and `Session`.

[Unreleased]: https://github.com/octaspace/python-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/octaspace/python-sdk/releases/tag/v0.1.0
