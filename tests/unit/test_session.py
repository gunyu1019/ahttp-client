import asyncio
from typing import get_type_hints

import aiohttp
import pytest

from ahttp_client import AsyncSession, Response, Session, get
from ahttp_client.backend.base import SyncBackend
from ahttp_client.enum import DirectResponseType
from ahttp_client.session import BaseSession


def test_async_session_rejects_duplicate_public_request_names() -> None:
    with pytest.raises(ValueError, match="Request name duplicate is duplicated"):

        class DuplicateNameSession(AsyncSession):
            @get("/first", name="duplicate")
            async def first(self, response: Response) -> None:
                pass

            @get("/second", name="duplicate")
            async def second(self, response: Response) -> None:
                pass


def test_sync_session_allows_overriding_the_same_python_attribute() -> None:
    class ParentSession(Session):
        @get("/parent", name="operation")
        def operation(self, response: Response) -> None:
            pass

    class ChildSession(ParentSession):
        @get("/child", name="operation")
        def operation(self, response: Response) -> None:
            pass

    assert ChildSession.operation.path == "/child"


def test_sessions_accept_direct_response_type() -> None:
    expected_type = DirectResponseType | bool

    assert get_type_hints(BaseSession.__init__)["directly_response"] == expected_type
    assert get_type_hints(AsyncSession.__init__)["directly_response"] == expected_type
    assert get_type_hints(Session.__init__)["directly_response"] == expected_type


def test_sync_backend_rejects_async_client_type() -> None:
    with pytest.raises(TypeError, match="not supported by SyncBackend"):
        SyncBackend.from_session(
            aiohttp.ClientSession,
            base_url="http://example.test",
        )


def test_async_session_rejects_sync_request_handler() -> None:
    with pytest.raises(TypeError, match="must use a asynchronous handler"):

        class InvalidSession(AsyncSession):
            @get("/")
            def endpoint(self) -> None:
                pass


def test_sync_session_rejects_async_request_handler() -> None:
    with pytest.raises(TypeError, match="must use a synchronous handler"):

        class InvalidSession(Session):
            @get("/")
            async def endpoint(self) -> None:
                pass


def test_session_rejects_combined_direct_response_modes() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        BaseSession.__init__(
            object.__new__(AsyncSession),
            "http://example.test",
            directly_response=DirectResponseType.RESPONSE | DirectResponseType.DESERIALIZED,
        )


def test_aiohttp_session_preserves_base_url_path_prefix() -> None:
    async def scenario() -> None:
        session = AsyncSession(
            "http://example.test/api",
            aiohttp.ClientSession,
        )
        try:
            request_path = session._get_request_url("/users")
            built_url = session.backend.session._build_url(request_path)

            assert session.base_url == "http://example.test/api/"
            assert request_path == "users"
            assert str(built_url) == "http://example.test/api/users"
        finally:
            await session.close()

    asyncio.run(scenario())


def test_async_session_can_be_constructed_before_event_loop() -> None:
    session = AsyncSession(
        "http://example.test",
        aiohttp.ClientSession,
    )

    assert session.closed is False
    asyncio.run(session.close())
    assert session.closed is True


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "example.test",
        "/relative",
        "ftp://example.test",
        "https:///missing-host",
    ],
)
def test_session_rejects_invalid_base_url(base_url: str) -> None:
    with pytest.raises(ValueError, match=r"absolute HTTP\(S\) URL"):
        BaseSession.__init__(object.__new__(AsyncSession), base_url)


def test_async_session_raises_consistent_error_after_close() -> None:
    async def scenario() -> None:
        session = AsyncSession(
            "http://example.test",
            aiohttp.ClientSession,
        )
        await session.close()

        with pytest.raises(RuntimeError, match="Session is closed"):
            await session.get("/users")

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "path",
    [
        "https://other.test/users",
        "//other.test/users",
        "../users",
        "users#fragment",
    ],
)
def test_session_rejects_paths_outside_base_url(path: str) -> None:
    session = object.__new__(AsyncSession)
    BaseSession.__init__(session, "http://example.test/api")
    session.backend = type("Backend", (), {"native_base_url": True})()

    with pytest.raises(ValueError):
        session._get_request_url(path)
