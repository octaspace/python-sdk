"""Which requests can be sent again, and how long to wait before that."""

from __future__ import annotations

import random

import httpx

# Repeating these changes nothing on the API side.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})

# Failures before the request leaves the client: resending cannot run it twice.
NOT_SENT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


def is_idempotent(method: str, idempotent: bool = False) -> bool:
    """Whether a request can be repeated without changing the outcome."""
    return idempotent or method.upper() in IDEMPOTENT_METHODS


def is_retryable_response(method: str, status_code: int, idempotent: bool = False) -> bool:
    """Whether a response with this status is worth repeating for this request."""
    return is_idempotent(method, idempotent) and status_code in RETRYABLE_STATUSES


def can_resend(method: str, error: httpx.TransportError, idempotent: bool = False) -> bool:
    """Whether a request that failed with ``error`` can safely be sent again."""
    return is_idempotent(method, idempotent) or isinstance(error, NOT_SENT_ERRORS)


def compute_backoff(
    *,
    attempt: int,
    retry_interval: float,
    backoff_factor: float,
    retry_after: int | None = None,
    jitter: float = 0.1,
) -> float:
    """Seconds to wait before the next attempt; ``retry_after`` takes precedence."""
    if retry_after is not None:
        return max(float(retry_after), 0.0)
    return retry_interval * (backoff_factor**attempt) + random.uniform(0.0, jitter)
