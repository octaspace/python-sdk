from __future__ import annotations

from collections.abc import Generator

import pytest

import octaspace
from octaspace import OctaSpaceClient


@pytest.fixture(autouse=True)
def reset_global_state() -> Generator[None, None, None]:
    octaspace.reset_configuration()
    yield
    octaspace.reset_configuration()


@pytest.fixture
def client() -> Generator[OctaSpaceClient, None, None]:
    with OctaSpaceClient(api_key="octa_ak_test", max_retries=0) as instance:
        yield instance


@pytest.fixture
def anonymous() -> Generator[OctaSpaceClient, None, None]:
    with OctaSpaceClient(max_retries=0) as instance:
        yield instance
