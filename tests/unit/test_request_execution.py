from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ahttp_client import Response, request
from ahttp_client.enum import DirectResponseType


class _RawResponse:
    def __init__(self) -> None:
        self.closed = False


class _SyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    def response_close(self, response: _RawResponse) -> None:
        response.closed = True


class _AsyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    async def response_close(self, response: _RawResponse) -> None:
        response.closed = True


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

    def _make_request(self, request_core, path: str) -> Response:
        return self.response


class _AsyncSession:
    def __init__(self, directly_response: DirectResponseType | bool) -> None:
        self.directly_response = directly_response
        self.response = Response(_RawResponse(), _AsyncBackend())
        self.response.payload = "payload"

    async def _make_request(self, request_core, path: str) -> Response:
        return self.response


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
