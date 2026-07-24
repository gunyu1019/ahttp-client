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
"""

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
