"""MIT License

Copyright (c) 2023-present gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

End-to-end coverage for one-shot async and synchronous sessions.
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

import pytest

from ahttp_client import AsyncSession, Query, Response, Session, get
from tests.backend_integration.backend_matrix import (
    ASYNC_BACKEND_IDS,
    ASYNC_BACKENDS,
    SYNC_BACKEND_IDS,
    SYNC_BACKENDS,
)


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_single_session_executes_request_and_closes(backend: type, base_url: str) -> None:
    clients: list[AsyncSession] = []

    @AsyncSession.single_session(base_url, backend)
    @get("/echo")
    async def one_shot(
        session: AsyncSession,
        value: Annotated[str, Query],
        response: Response,
    ) -> dict[str, Any]:
        clients.append(session)
        return response.json()

    payload = asyncio.run(one_shot("once"))
    assert payload["query"] == {"value": ["once"]}
    assert len(clients) == 1
    assert clients[0].closed is True


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_single_session_executes_request_and_closes(backend: type, base_url: str) -> None:
    clients: list[Session] = []

    @Session.single_session(base_url, backend)
    @get("/echo")
    def one_shot(
        session: Session,
        value: Annotated[str, Query],
        response: Response,
    ) -> dict[str, Any]:
        clients.append(session)
        return response.json()

    payload = one_shot("once")
    assert payload["query"] == {"value": ["once"]}
    assert len(clients) == 1
    assert clients[0].closed is True


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_single_session_closes_after_user_exception(backend: type, base_url: str) -> None:
    clients: list[AsyncSession] = []

    @AsyncSession.single_session(base_url, backend)
    @get("/echo")
    async def one_shot(session: AsyncSession, response: Response) -> None:
        clients.append(session)
        raise LookupError("intentional failure")

    with pytest.raises(LookupError, match="intentional failure"):
        asyncio.run(one_shot())
    assert len(clients) == 1
    assert clients[0].closed is True


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_single_session_closes_after_user_exception(backend: type, base_url: str) -> None:
    clients: list[Session] = []

    @Session.single_session(base_url, backend)
    @get("/echo")
    def one_shot(session: Session, response: Response) -> None:
        clients.append(session)
        raise LookupError("intentional failure")

    with pytest.raises(LookupError, match="intentional failure"):
        one_shot()
    assert len(clients) == 1
    assert clients[0].closed is True
