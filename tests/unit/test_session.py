from typing import get_type_hints

import pytest

from ahttp_client import AsyncSession, Response, Session, get
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
