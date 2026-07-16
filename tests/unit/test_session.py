import pytest

from ahttp_client import AsyncSession, Response, Session, get


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
