from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import quote

from .._transport.base import AuthMode, BaseTransport


class Resource:
    """Base class of the resources; sends requests through the client's transport."""

    def __init__(self, transport: BaseTransport) -> None:
        self._transport = transport

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        auth: AuthMode = "required",
        idempotent: bool = False,
    ) -> Any:
        """Send a request and return its parsed JSON body (``None`` when it has none)."""
        response = self._transport.request(
            method, path, params=params, body=body, auth=auth, idempotent=idempotent
        )
        return response.data


def segment(value: str) -> str:
    """Escape a path segment, such as a session UUID or a node number."""
    return quote(str(value), safe="")


def pick(values: Mapping[str, Any], allowed: Iterable[str], what: str) -> dict[str, Any]:
    """Keep the values that are not ``None``; raise ``TypeError`` for a key not in ``allowed``.

    The API refuses unknown fields, so a misspelt one fails here, before anything is sent.
    """
    allowed = tuple(allowed)
    unknown = sorted(key for key in values if key not in allowed)
    if unknown:
        raise TypeError(f"{what} got unknown field(s): {', '.join(unknown)}")
    return {key: value for key, value in values.items() if value is not None}


def with_batch_ids(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Give every batch item an id, its position by default; raise ``TypeError`` on duplicates."""
    result: list[dict[str, Any]] = []
    seen: set[Any] = set()
    for index, item in enumerate(items):
        entry = dict(item)
        if entry.get("id") is None:
            entry["id"] = index
        if entry["id"] in seen:
            raise TypeError(
                f"Duplicate batch id {entry['id']!r}: give every item a unique id, "
                "or none to all of them"
            )
        seen.add(entry["id"])
        result.append(entry)
    return result
