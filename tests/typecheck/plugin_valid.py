from __future__ import annotations

from typing import assert_type

from ahttp_client.enum import DirectResponseType
from ahttp_client.request import get, post
from ahttp_client.session import AsyncSession, Session


class AsyncDeclarativeAPI(AsyncSession):
    @get("/ellipsis", directly_response=True)
    async def ellipsis_body(self) -> dict[str, int]:
        ...

    @get("/enum", directly_response=DirectResponseType.RESPONSE)
    async def enum_direct_body(self) -> object:
        pass

    @get("/handled")
    async def regular_handler(self) -> str:  # type: ignore[empty-body]
        pass


class SyncDeclarativeAPI(Session):
    @post("/pass", directly_response=True)
    def pass_body(self) -> dict[str, int]:
        pass


class CustomAsyncSession(AsyncSession):
    pass


class InheritedDeclarativeAPI(CustomAsyncSession):
    @get("/inherited", directly_response=True)
    async def inherited_body(self) -> str:
        ...


async def check_async_endpoint_types(api: AsyncDeclarativeAPI) -> None:
    assert_type(await api.ellipsis_body(), dict[str, int])
    await api.ellipsis_body(unexpected=True)  # type: ignore[call-arg]


def check_sync_endpoint_types(api: SyncDeclarativeAPI) -> None:
    assert_type(api.pass_body(), dict[str, int])
    api.pass_body(unexpected=True)  # type: ignore[call-arg]
