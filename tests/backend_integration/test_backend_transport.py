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

On-the-wire request conversion coverage for every supported backend.
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Annotated, Any

import pytest

from ahttp_client import (
    AsyncSession,
    Body,
    BodyForm,
    BodyJson,
    Response,
    Session,
    post,
)
from tests.backend_integration.backend_matrix import (
    ASYNC_BACKEND_IDS,
    ASYNC_BACKENDS,
    BACKEND_BY_SESSION,
    SYNC_BACKEND_IDS,
    SYNC_BACKENDS,
)

FILE_CONTENT = "첨부 파일".encode()


class AsyncTransportAPI(AsyncSession):
    @post("/echo")
    async def json_body(self, value: Annotated[dict[str, Any], BodyJson], response: Response) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def raw_body(self, value: Annotated[bytes, Body], response: Response) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def raw_file_body(
        self,
        document: Annotated[io.BytesIO, Body.metadata("report.txt", "text/plain")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def multipart_body(
        self,
        description: BodyForm,
        document: Annotated[bytes, BodyForm.metadata("한글-report.txt", "text/plain")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


class SyncTransportAPI(Session):
    @post("/echo")
    def json_body(self, value: Annotated[dict[str, Any], BodyJson], response: Response) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def raw_body(self, value: Annotated[bytes, Body], response: Response) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def raw_file_body(
        self,
        document: Annotated[io.BytesIO, Body.metadata("report.txt", "text/plain")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def multipart_body(
        self,
        description: BodyForm,
        document: Annotated[bytes, BodyForm.metadata("한글-report.txt", "text/plain")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


async def _async_call(backend: type, base_url: str, method_name: str, *args: Any) -> dict[str, Any]:
    async with AsyncTransportAPI(base_url, backend) as api:
        return await getattr(api, method_name)(*args)


def _sync_call(backend: type, base_url: str, method_name: str, *args: Any) -> dict[str, Any]:
    with SyncTransportAPI(base_url, backend) as api:
        return getattr(api, method_name)(*args)


def _assert_json(payload: dict[str, Any]) -> None:
    assert payload["content_type"] == "application/json"
    assert payload["json"] == {"value": {"item": {"name": "notebook"}}}


def _assert_raw(payload: dict[str, Any], body: bytes) -> None:
    assert payload["raw_base64"] == base64.b64encode(body).decode("ascii")


def _assert_multipart(payload: dict[str, Any]) -> None:
    assert payload["content_type"] == "multipart/form-data"
    assert payload["form"] == {"description": ["quarterly report"]}
    assert payload["files"] == {
        "document": [
            {
                "filename": "한글-report.txt",
                "content_type": "text/plain",
                "base64": base64.b64encode(FILE_CONTENT).decode("ascii"),
            }
        ]
    }


def _capture_request_kwargs(monkeypatch: pytest.MonkeyPatch, session_type: type) -> list[dict[str, Any]]:
    backend_type = BACKEND_BY_SESSION[session_type]
    original = backend_type.get_request_kwargs
    captured: list[dict[str, Any]] = []

    def capture(self: Any, request_obj: Any) -> dict[str, Any]:
        request_kwargs = original(self, request_obj)
        snapshot = dict(request_kwargs)
        form_data = snapshot.get("data")
        if hasattr(form_data, "_is_multipart") and hasattr(form_data, "_fields"):
            snapshot["data"] = {
                "is_multipart": form_data._is_multipart,
                "field_count": len(form_data._fields),
            }
        captured.append(snapshot)
        return request_kwargs

    monkeypatch.setattr(backend_type, "get_request_kwargs", capture)
    return captured


def _assert_request_kwargs(
    session_type: type,
    captured: list[dict[str, Any]],
    raw_file: io.BytesIO,
) -> None:
    json_kwargs, raw_kwargs, raw_file_kwargs, multipart_kwargs = captured
    assert json_kwargs["json"] == {"value": {"item": {"name": "notebook"}}}

    raw_key = "content" if "content" in raw_kwargs else "data"
    assert raw_kwargs[raw_key] == b"raw\x00body"
    assert raw_file_kwargs["headers"] == {
        "Content-Type": "text/plain",
        "Content-Disposition": 'attachment; filename="report.txt"',
    }
    if raw_key == "content":
        assert raw_file_kwargs[raw_key] == b"file content"
    else:
        assert raw_file_kwargs[raw_key] is raw_file

    if "data" in multipart_kwargs:
        form_data = multipart_kwargs["data"]
        assert form_data == {"is_multipart": True, "field_count": 2}
    else:
        assert multipart_kwargs["files"] == {
            "description": (None, "quarterly report"),
            "document": ("한글-report.txt", FILE_CONTENT, "text/plain"),
        }


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_backends_convert_payloads_on_the_wire(
    backend: type, base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_request_kwargs(monkeypatch, backend)
    _assert_json(asyncio.run(_async_call(backend, base_url, "json_body", {"item": {"name": "notebook"}})))
    _assert_raw(
        asyncio.run(_async_call(backend, base_url, "raw_body", b"raw\x00body")),
        b"raw\x00body",
    )
    raw_file = io.BytesIO(b"file content")
    raw_file_payload = asyncio.run(_async_call(backend, base_url, "raw_file_body", raw_file))
    _assert_raw(raw_file_payload, b"file content")
    raw_file_headers = {key.lower(): value for key, value in raw_file_payload["headers"].items()}
    assert raw_file_headers["content-type"] == "text/plain"
    assert raw_file_headers["content-disposition"] == 'attachment; filename="report.txt"'
    _assert_multipart(asyncio.run(_async_call(backend, base_url, "multipart_body", "quarterly report", FILE_CONTENT)))
    _assert_request_kwargs(backend, captured, raw_file)


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_backends_convert_payloads_on_the_wire(
    backend: type, base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_request_kwargs(monkeypatch, backend)
    _assert_json(_sync_call(backend, base_url, "json_body", {"item": {"name": "notebook"}}))
    _assert_raw(_sync_call(backend, base_url, "raw_body", b"raw\x00body"), b"raw\x00body")
    raw_file = io.BytesIO(b"file content")
    raw_file_payload = _sync_call(backend, base_url, "raw_file_body", raw_file)
    _assert_raw(raw_file_payload, b"file content")
    raw_file_headers = {key.lower(): value for key, value in raw_file_payload["headers"].items()}
    assert raw_file_headers["content-type"] == "text/plain"
    assert raw_file_headers["content-disposition"] == 'attachment; filename="report.txt"'
    _assert_multipart(_sync_call(backend, base_url, "multipart_body", "quarterly report", FILE_CONTENT))
    _assert_request_kwargs(backend, captured, raw_file)
