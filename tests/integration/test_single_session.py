"""End-to-end coverage for one-shot async and synchronous sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

import pytest

from ahttp_client import AsyncSession, Query, Response, Session, get
from tests.integration.backend_matrix import (
    ASYNC_BACKEND_IDS,
    ASYNC_BACKENDS,
    SYNC_BACKEND_IDS,
    SYNC_BACKENDS,
)


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_single_session_executes_request_and_closes(
    backend: type, base_url: str
) -> None:
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


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_single_session_executes_request_and_closes(
    backend: type, base_url: str
) -> None:
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


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_single_session_closes_after_user_exception(
    backend: type, base_url: str
) -> None:
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


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_single_session_closes_after_user_exception(
    backend: type, base_url: str
) -> None:
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
