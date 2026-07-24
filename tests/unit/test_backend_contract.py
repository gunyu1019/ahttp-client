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
import ssl
from abc import abstractmethod
from types import SimpleNamespace
from typing import Any
import warnings

import pytest

from ahttp_client import BaseSession, request
from ahttp_client.backend.aiohttp import AiohttpBackend
from ahttp_client.backend.base import AsyncBackend, BaseBackend
from ahttp_client.backend.requests import RequestsBackend


def test_request_kwargs_preserve_non_copyable_native_objects() -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    @request("GET", "/", ssl=context)
    def endpoint(_: BaseSession) -> None:
        pass

    backend = object.__new__(AiohttpBackend)
    request_kwargs = backend.get_request_kwargs(endpoint.copy())

    assert request_kwargs["ssl"] is context


def test_httpx_empty_json_response_returns_none() -> None:
    httpx = pytest.importorskip("httpx")
    from ahttp_client.backend.httpx import HttpXSyncSession

    response = httpx.Response(204, content=b"")
    backend = object.__new__(HttpXSyncSession)

    assert backend.response_json(response) is None


def test_custom_json_parsers_receive_bytes_on_every_backend() -> None:
    httpx = pytest.importorskip("httpx")
    requests = pytest.importorskip("requests")
    from ahttp_client.backend.httpx import HttpXSyncSession
    from ahttp_client.backend.requests import RequestsBackend

    payload = b'{"value": 1}'
    aiohttp_response = SimpleNamespace(_body=payload)
    httpx_response = httpx.Response(200, content=payload)
    requests_response = requests.Response()
    requests_response._content = payload

    def input_type(value: Any) -> type[Any]:
        return type(value)

    assert object.__new__(AiohttpBackend).response_json(aiohttp_response, input_type) is bytes
    assert object.__new__(HttpXSyncSession).response_json(httpx_response, input_type) is bytes
    assert object.__new__(RequestsBackend).response_json(requests_response, input_type) is bytes


def test_registered_client_subclass_uses_nearest_backend() -> None:
    aiohttp = pytest.importorskip("aiohttp")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        class CustomClientSession(aiohttp.ClientSession):
            pass

    async def scenario() -> None:
        backend = AsyncBackend.from_session(
            CustomClientSession,
            base_url="http://example.test/",
        )
        try:
            assert isinstance(backend, AiohttpBackend)
            assert isinstance(backend.session, CustomClientSession)
        finally:
            await backend.session_close()

    asyncio.run(scenario())


def test_backend_registration_rejects_implicit_replacement() -> None:
    class FakeSession:
        pass

    try:
        class OriginalBackend(RequestsBackend):
            session_cls = FakeSession
            response_cls = object

        with pytest.raises(RuntimeError, match="already registered"):

            class DuplicateBackend(RequestsBackend):
                session_cls = FakeSession
                response_cls = object

        class ExplicitReplacementBackend(RequestsBackend):
            session_cls = FakeSession
            response_cls = object
            replace_registered_backend = True

        assert BaseBackend._registry[FakeSession] is ExplicitReplacementBackend
    finally:
        BaseBackend._registry.pop(FakeSession, None)


def test_abstract_backend_is_not_registered() -> None:
    class FakeSession:
        pass

    try:
        class AbstractBackend(RequestsBackend):
            session_cls = FakeSession
            response_cls = object

            @abstractmethod
            def extension_point(self) -> None:
                pass

        assert FakeSession not in BaseBackend._registry
    finally:
        BaseBackend._registry.pop(FakeSession, None)
