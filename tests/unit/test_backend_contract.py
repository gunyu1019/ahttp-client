from __future__ import annotations

import ssl
from types import SimpleNamespace
from typing import Any

import pytest

from ahttp_client import BaseSession, request
from ahttp_client.backend.aiohttp import AiohttpBackend


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
