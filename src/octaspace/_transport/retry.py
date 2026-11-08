"""Which requests can be sent again, and how long to wait before that."""

from __future__ import annotations

import random

import httpx

IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})

# Failures before the request leaves the client: resending cannot run it twice.
NOT_SENT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


def is_retryable_response(method: str, status_code: int) -> bool:
    """Whether a response with this status is worth repeating for this method."""
    return method.upper() in IDEMPOTENT_METHODS and status_code in RETRYABLE_STATUSES


def can_resend(method: str, error: httpx.TransportError) -> bool:
    """Whether a request that failed with ``error`` can safely be sent again."""
    return method.upper() in IDEMPOTENT_METHODS or isinstance(error, NOT_SENT_ERRORS)


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
