from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"
API = "https://api.octa.space"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text())


def sent_json(route: Any, call: int = -1) -> Any:
    request: httpx.Request = route.calls[call].request
    return json.loads(request.content) if request.content else None
