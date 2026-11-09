# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `ConflictError` for HTTP 409.
- The `max_retry_after` option (`OCTA_MAX_RETRY_AFTER`): the longest
  `Retry-After` the client waits for, 60 seconds by default.
- `Retry-After` given as an HTTP date.

### Changed

- HTTP 400 raises `ValidationError` instead of `APIError`.
- GET, PUT and DELETE requests are retried after connection errors and
  timeouts, not only after error responses.
- `ConfigurationError` is also a `ValueError`; invalid `OCTA_*` numbers raise
  it.
- Any transport failure raises `APIConnectionError` or `APITimeoutError`
  instead of an `httpx` exception.

- **Breaking:** Python 3.11 or later is required; Python 3.10 is no longer
  supported.

### Removed

- **Breaking:** the `octaspace-smoke` command and `python -m octaspace`.

### Fixed

- With several API hosts, a request that changes something (starting or
  stopping a session, setting prices) is no longer sent to another host after
  a timeout, so that it cannot run twice.
- The API token no longer appears in `repr()` of `ClientConfig`.

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
