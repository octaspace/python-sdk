from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Session:
    """A session, built from an item of ``sessions.list().data``."""

    uuid: str
    service: str
    app_name: str | None
    node_id: int | None
    urls: list[str]
    prices: dict[str, Any]
    node_hw: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        node_id = data.get("node_id")
        return cls(
            uuid=str(data["uuid"]),
            service=str(data.get("service", "")),
            app_name=data.get("app_name"),
            node_id=int(node_id) if node_id is not None else None,
            urls=list(data.get("urls", [])),
            prices=dict(data.get("prices", {})),
            node_hw=dict(data.get("node_hw", {})),
        )
