from __future__ import annotations

import io
from typing import Annotated

import pytest

from ahttp_client import BaseSession, Body, BodyType, request
from ahttp_client.backend.aiohttp import AiohttpBackend
from ahttp_client.backend.httpx import HttpXAsyncSession
from ahttp_client.backend.requests import RequestsBackend


def _filled_request(request_core, value):
    bound_arguments = request_core._signature.bind(None, value)
    filled_request = request_core.copy()
    filled_request._fill_parameter(None, bound_arguments)
    return filled_request


@pytest.mark.parametrize(
    "backend_type, body_key",
    [
        (AiohttpBackend, "data"),
        (HttpXAsyncSession, "content"),
        (RequestsBackend, "data"),
    ],
)
def test_body_multipart_adds_metadata_to_raw_file(backend_type, body_key):
    @request("POST", "/uploads")
    async def upload(
        _: BaseSession,
        document: Annotated[io.BytesIO, Body.metadata("report.txt", "text/plain")],
    ) -> None:
        pass

    document = io.BytesIO(b"file content")
    filled_request = _filled_request(upload, document)

    assert upload.body_type == BodyType.RAW
    assert filled_request.body is document
    assert filled_request._body_file is None
    assert filled_request.body_parameter.is_file_type is True
    assert filled_request.headers == {
        "Content-Type": "text/plain",
        "Content-Disposition": 'attachment; filename="report.txt"',
    }

    backend = object.__new__(backend_type)
    request_kwargs = backend.get_request_kwargs(filled_request)

    assert set(request_kwargs) == {"headers", body_key}
    assert request_kwargs["headers"] == filled_request.headers
    if body_key == "content":
        assert request_kwargs[body_key] == b"file content"
    else:
        assert request_kwargs[body_key] is document


@pytest.mark.parametrize(
    "backend_type, body_key",
    [
        (AiohttpBackend, "data"),
        (HttpXAsyncSession, "content"),
        (RequestsBackend, "data"),
    ],
)
def test_file_like_body_remains_raw(backend_type, body_key):
    @request("POST", "/uploads")
    async def upload(_: BaseSession, document: Annotated[io.BytesIO, Body]) -> None:
        pass

    document = io.BytesIO(b"file content")
    filled_request = _filled_request(upload, document)

    assert upload.body_type == BodyType.RAW
    assert filled_request.body is document
    assert filled_request._body_file is None
    assert filled_request.body_parameter.is_file_type is True

    backend = object.__new__(backend_type)
    request_kwargs = backend.get_request_kwargs(filled_request)

    assert set(request_kwargs) == {body_key}
    if body_key == "content":
        assert request_kwargs[body_key] == b"file content"
    else:
        assert request_kwargs[body_key] is document
