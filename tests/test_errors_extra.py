from __future__ import annotations

import httpx

from octaspace.errors import APIError, ServerError, error_context, from_response
from octaspace.response import APIResponse


def test_error_message_fallback_and_context() -> None:
    response = APIResponse.from_httpx(httpx.Response(400, json={}))
    error = from_response(response)

    assert isinstance(error, APIError)
    assert str(error) == "Request failed with status 400"
    assert error_context(error)["status_code"] == 400
    assert error_context(RuntimeError("boom")) == {"message": "boom"}


def test_error_mapping_for_unmapped_server_error() -> None:
    response = APIResponse.from_httpx(httpx.Response(501, json={"detail": "not implemented"}))
    error = from_response(response)

    assert isinstance(error, ServerError)
    assert str(error) == "not implemented"
