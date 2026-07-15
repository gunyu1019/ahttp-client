from __future__ import annotations

import asyncio
import io
from typing import Annotated

import pytest

from ahttp_client import (
    BaseSession,
    BodyForm,
    BodyFormEncoding,
    BodyJson,
    BodyType,
    request,
)
from ahttp_client.backend.aiohttp import AiohttpBackend
from ahttp_client.backend.httpx import HttpXSyncSession
from ahttp_client.backend.requests import RequestsBackend


def _filled_request(request_core, *values):
    bound_arguments = request_core._signature.bind(None, *values)
    bound_arguments.apply_defaults()
    filled_request = request_core.copy()
    filled_request._fill_parameter(None, bound_arguments)
    return filled_request


def test_body_json_builds_nested_and_renamed_payload():
    @request("POST", "/items")
    async def create_item(
        _: BaseSession,
        name: Annotated[str, BodyJson.custom_key("item.name")],
        quantity: Annotated[int, BodyJson.custom_key("item.quantity")],
        send_email: Annotated[bool, BodyJson.custom_name("sendEmail")],
    ) -> None:
        pass

    filled_request = _filled_request(create_item, "notebook", 2, True)

    assert create_item.body_type == BodyType.JSON
    assert set(create_item.body_json_parameter) == {"name", "quantity", "sendEmail"}
    assert filled_request.body == {
        "item": {"name": "notebook", "quantity": 2},
        "sendEmail": True,
    }


def test_body_form_defaults_to_url_encoded_without_file_fields():
    @request("POST", "/tokens")
    async def create_token(
        _: BaseSession,
        client_id: Annotated[str, BodyForm.to_camel()],
        scope: BodyForm,
    ) -> None:
        pass

    filled_request = _filled_request(create_token, "client-1", "read write")

    assert create_token.body_type == BodyType.URL_ENCODED
    assert filled_request.body == {"clientId": "client-1", "scope": "read write"}
    assert filled_request._body_file is None


def test_body_form_file_field_selects_multipart_and_preserves_metadata():
    @request("POST", "/uploads")
    async def upload(
        _: BaseSession,
        description: BodyForm,
        document: Annotated[bytes, BodyForm.metadata("report.txt", "text/plain")],
    ) -> None:
        pass

    filled_request = _filled_request(upload, "quarterly report", b"file content")

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body == {"description": "quarterly report"}
    assert filled_request._body_file == {
        "document": ("report.txt", b"file content", "text/plain"),
    }


@pytest.mark.parametrize(
    "backend_type, body_key",
    [
        (AiohttpBackend, "data"),
        (HttpXSyncSession, "files"),
        (RequestsBackend, "files"),
    ],
)
def test_multipart_body_is_converted_for_each_backend(backend_type, body_key):
    @request("POST", "/uploads")
    async def upload(
        _: BaseSession,
        description: BodyForm,
        document: Annotated[bytes, BodyForm.metadata("report.txt", "text/plain")],
    ) -> None:
        pass

    filled_request = _filled_request(upload, "quarterly report", b"file content")
    backend = object.__new__(backend_type)
    request_kwargs = backend.get_request_kwargs(filled_request)

    assert set(request_kwargs) == {body_key}
    if body_key == "files":
        assert request_kwargs["files"] == {
            "description": (None, "quarterly report"),
            "document": ("report.txt", b"file content", "text/plain"),
        }
    else:
        form_data = request_kwargs["data"]
        assert form_data._is_multipart is True
        assert len(form_data._fields) == 2


def test_aiohttp_multipart_preserves_non_ascii_filename():
    @request("POST", "/uploads")
    async def upload(
        _: BaseSession,
        document: Annotated[
            bytes,
            BodyForm.metadata("한글-file.txt", "text/plain"),
        ],
    ) -> None:
        pass

    filled_request = _filled_request(upload, b"file content")
    form_data = object.__new__(AiohttpBackend).get_request_kwargs(filled_request)["data"]
    multipart = form_data()

    class BufferWriter:
        def __init__(self) -> None:
            self.data = bytearray()

        async def write(self, chunk: bytes) -> None:
            self.data.extend(chunk)

    writer = BufferWriter()
    asyncio.run(multipart.write(writer))

    assert 'filename="한글-file.txt"'.encode() in writer.data
    assert b"%ED%95%9C%EA%B8%80-file.txt" not in writer.data


def test_file_like_body_form_field_uses_multipart_automatically():
    @request("POST", "/uploads")
    async def upload(_: BaseSession, document: Annotated[io.BytesIO, BodyForm]) -> None:
        pass

    document = io.BytesIO(b"file content")
    filled_request = _filled_request(upload, document)

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body is None
    assert filled_request._body_file == {"document": ("document", document, None)}


def test_form_encoding_can_force_multipart_without_file_fields():
    @request("POST", "/uploads", form_encoding=BodyFormEncoding.FORM_DATA)
    async def upload(_: BaseSession, description: BodyForm) -> None:
        pass

    filled_request = _filled_request(upload, "quarterly report")

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body == {"description": "quarterly report"}
    assert filled_request._body_file is None
