from __future__ import annotations

import httpx

from octaspace._transport.retry import can_resend, compute_backoff, is_retryable_response


def test_retryable_statuses() -> None:
    assert is_retryable_response("GET", 503) is True
    assert is_retryable_response("GET", 500) is False
    assert is_retryable_response("POST", 503) is False
    assert is_retryable_response("POST", 503, idempotent=True) is True
    assert is_retryable_response("DELETE", 429) is True
    assert is_retryable_response("PATCH", 429) is False


def test_resend_after_a_transport_error() -> None:
    assert can_resend("POST", httpx.ConnectError("refused")) is True
    assert can_resend("POST", httpx.ReadTimeout("slow")) is False
    assert can_resend("POST", httpx.ReadTimeout("slow"), idempotent=True) is True


def test_retry_after_overrides_backoff() -> None:
    assert compute_backoff(attempt=2, retry_interval=0.5, backoff_factor=2.0, retry_after=15) == 15
