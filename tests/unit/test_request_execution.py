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

import asyncio
from typing import Any

import pytest

from ahttp_client import Response, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.exception import HTTPException


class _RawResponse:
    def __init__(self) -> None:
        self.closed = False
        self.status = 200
        self.url = "https://example.test/"


class _SyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    def response_close(self, response: _RawResponse) -> None:
        response.closed = True

    def response_status(self, response: _RawResponse) -> int:
        return response.status

    def response_url(self, response: _RawResponse) -> str:
        return response.url


class _AsyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    async def response_close(self, response: _RawResponse) -> None:
        response.closed = True

    def response_status(self, response: _RawResponse) -> int:
        return response.status

    def response_url(self, response: _RawResponse) -> str:
        return response.url


def test_async_close_supports_synchronous_backend_close() -> None:
    response = Response(_RawResponse(), _SyncBackend())

    asyncio.run(response.async_close())

    assert response.closed is True


class _Deserializer:
    def get_data(self, response: Response) -> Any:
        return response.payload

    def deserialize(self, data: Any) -> dict[str, Any]:
        return {"deserialized": data}


class _SyncSession:
    def __init__(self, directly_response: DirectResponseType | bool) -> None:
        self.directly_response = directly_response
        self.response = Response(_RawResponse(), _SyncBackend())
        self.response.payload = "payload"

    def _make_request(self, request_core, path: str) -> tuple[Response, Any]:
        raw = self.response
        resp: Any = raw
        if self._has_overridden_method(self.after_request):
            resp = self.after_request(raw)
        return raw, resp

    def _has_overridden_method(self, method) -> bool:
        return type(self).after_request is not _SyncSession.after_request

    def after_request(self, response: Response) -> Any:
        return response


class _AsyncSession:
    def __init__(self, directly_response: DirectResponseType | bool) -> None:
        self.directly_response = directly_response
        self.response = Response(_RawResponse(), _AsyncBackend())
        self.response.payload = "payload"

    async def _make_request(self, request_core, path: str) -> tuple[Response, Any]:
        raw = self.response
        resp: Any = raw
        if self._has_overridden_method(self.after_request):
            resp = await self.after_request(raw)
        return raw, resp

    def _has_overridden_method(self, method) -> bool:
        return type(self).after_request is not _AsyncSession.after_request

    async def after_request(self, response: Response) -> Any:
        return response


class _TransformingSyncSession(_SyncSession):
    def after_request(self, response: Response) -> dict[str, str]:
        return {"transformed": response.payload}


class _TransformingAsyncSession(_AsyncSession):
    async def after_request(self, response: Response) -> dict[str, str]:
        return {"transformed": response.payload}


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_raise_on_rejects_every_status_except_200(is_async: bool) -> None:
    if is_async:

        @request("GET", "/", raise_on=True)
        async def endpoint(session) -> None: ...

        session = _AsyncSession(DirectResponseType.RESPONSE)
        session.response.raw.status = 201
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/", raise_on=True)
        def endpoint(session) -> None: ...

        session = _SyncSession(DirectResponseType.RESPONSE)
        session.response.raw.status = 201
        with pytest.raises(HTTPException) as exc_info:
            endpoint._execute(session)

    assert exc_info.value.status == 201
    assert exc_info.value.response is session.response
    assert session.response.closed is True


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_raise_on_defaults_to_false(is_async: bool) -> None:
    if is_async:

        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession(DirectResponseType.RESPONSE)
        session.response.raw.status = 201
        result = asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession(DirectResponseType.RESPONSE)
        session.response.raw.status = 201
        result = endpoint._execute(session)

    assert result is session.response


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_session_response_mode_returns_response_even_with_deserializer(
    is_async: bool,
) -> None:
    if is_async:

        @request("GET", "/")
        async def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _AsyncSession(DirectResponseType.RESPONSE)
        endpoint._deserializer = _Deserializer()
        result = asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/")
        def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _SyncSession(DirectResponseType.RESPONSE)
        endpoint._deserializer = _Deserializer()
        result = endpoint._execute(session)

    assert result is session.response
    assert result.closed is False


def test_handler_preserves_positional_only_arguments() -> None:
    @request("GET", "/")
    def endpoint(session, value: int, /) -> int:
        return value

    assert endpoint._execute(_SyncSession(False), 7) == 7


def test_handler_preserves_variadic_positional_arguments() -> None:
    @request("GET", "/")
    def endpoint(session, *values: int) -> tuple[int, ...]:
        return values

    assert endpoint._execute(_SyncSession(False), 1, 2) == (1, 2)


def test_handler_preserves_variadic_keyword_arguments() -> None:
    @request("GET", "/")
    def endpoint(session, **values: int) -> dict[str, int]:
        return values

    assert endpoint._execute(_SyncSession(False), one=1) == {"one": 1}


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_session_deserialized_mode_returns_model_and_closes_response(
    is_async: bool,
) -> None:
    if is_async:

        @request("GET", "/")
        async def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _AsyncSession(DirectResponseType.DESERIALIZED)
        endpoint._deserializer = _Deserializer()
        result = asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/")
        def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _SyncSession(DirectResponseType.DESERIALIZED)
        endpoint._deserializer = _Deserializer()
        result = endpoint._execute(session)

    assert result == {"deserialized": "payload"}
    assert session.response.closed is True


def test_request_direct_response_mode_overrides_session_mode() -> None:
    @request("GET", "/", directly_response=DirectResponseType.RESPONSE)
    def endpoint(session) -> None:
        raise AssertionError("direct response must skip the endpoint body")

    session = _SyncSession(DirectResponseType.DESERIALIZED)
    endpoint._deserializer = _Deserializer()

    result = endpoint._execute(session)

    assert result is session.response
    assert result.closed is False


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_session_after_hook_result_is_injected_and_raw_response_is_closed(
    is_async: bool,
) -> None:
    if is_async:

        @request("GET", "/")
        async def endpoint(session, response: Response) -> dict[str, str]:
            return response

        session = _TransformingAsyncSession(False)
        result = asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/")
        def endpoint(session, response: Response) -> dict[str, str]:
            return response

        session = _TransformingSyncSession(False)
        result = endpoint._execute(session)

    assert result == {"transformed": "payload"}
    assert session.response.closed is True


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_session_after_hook_result_is_returned_directly_and_raw_response_is_closed(
    is_async: bool,
) -> None:
    if is_async:

        @request("GET", "/")
        async def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _TransformingAsyncSession(DirectResponseType.RESPONSE)
        result = asyncio.run(endpoint._execute(session))
    else:

        @request("GET", "/")
        def endpoint(session) -> None:
            raise AssertionError("direct response must skip the endpoint body")

        session = _TransformingSyncSession(DirectResponseType.RESPONSE)
        result = endpoint._execute(session)

    assert result == {"transformed": "payload"}
    assert session.response.closed is True
