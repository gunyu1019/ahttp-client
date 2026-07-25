"""Fixtures shared by aiohttp serialization integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from tests.backend_integration.conftest import EchoServer


@pytest.fixture(scope="session")
def echo_server() -> Generator[EchoServer, None, None]:
    server = EchoServer().start()
    try:
        yield server
    finally:
        server.close()


@pytest.fixture(scope="session")
def base_url(echo_server: EchoServer) -> str:
    return echo_server.base_url
