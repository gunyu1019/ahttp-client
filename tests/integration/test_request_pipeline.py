"""On-the-wire component and body serialization coverage for every backend."""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Annotated, Any

import aiohttp
import httpx
import pytest
import requests

from ahttp_client import (
    AsyncSession,
    BodyForm,
    BodyFormEncoding,
    BodyJson,
    Header,
    Path,
    Query,
    Response,
    Session,
    get,
    post,
)

ASYNC_BACKENDS = (aiohttp.ClientSession, httpx.AsyncClient)
SYNC_BACKENDS = (httpx.Client, requests.Session)
ASYNC_BACKEND_IDS = ("aiohttp", "httpx_async")
SYNC_BACKEND_IDS = ("httpx_sync", "requests")
FILE_CONTENT = "inferred-file-한글".encode()


class AsyncPipelineAPI(AsyncSession):
    @get(
        "/echo/{resource}",
        params={"static_query": "kept"},
        headers={"X-Static": "kept"},
    )
    async def components(
        self,
        resource: Annotated[str, Path],
        basic_query: Annotated[str, Query],
        repeated_query: Annotated[list[str], Query],
        custom_query: Annotated[str, Query.custom_name("query-alias")],
        camel_query: Annotated[str, Query.to_camel()],
        pascal_query: Annotated[str, Query.to_pascal()],
        custom_header: Annotated[str, Header.custom_name("X-Custom")],
        camel_header: Annotated[str, Header.to_camel()],
        pascal_header: Annotated[str, Header.to_pascal()],
        response: Response,
        optional_query: Annotated[str | None, Query] = None,
        optional_header: Annotated[str | None, Header] = None,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def body_json(
        self,
        name: Annotated[str, BodyJson],
        city: Annotated[str, BodyJson.custom_key("profile.address.city")],
        enabled: Annotated[bool, BodyJson.custom_name("isEnabled")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def form_auto(
        self,
        username: Annotated[str, BodyForm],
        tags: Annotated[list[str], BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo", form_encoding=BodyFormEncoding.URL_ENCODED)
    async def form_urlencoded(
        self,
        first: Annotated[str, BodyForm.custom_name("first-name")],
        count: Annotated[int, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo", form_encoding=BodyFormEncoding.FORM_DATA)
    async def form_multipart_fields(
        self,
        title: Annotated[str, BodyForm],
        count: Annotated[int, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    async def form_inferred_file(
        self,
        upload: Annotated[io.BytesIO, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


class SyncPipelineAPI(Session):
    @get(
        "/echo/{resource}",
        params={"static_query": "kept"},
        headers={"X-Static": "kept"},
    )
    def components(
        self,
        resource: Annotated[str, Path],
        basic_query: Annotated[str, Query],
        repeated_query: Annotated[list[str], Query],
        custom_query: Annotated[str, Query.custom_name("query-alias")],
        camel_query: Annotated[str, Query.to_camel()],
        pascal_query: Annotated[str, Query.to_pascal()],
        custom_header: Annotated[str, Header.custom_name("X-Custom")],
        camel_header: Annotated[str, Header.to_camel()],
        pascal_header: Annotated[str, Header.to_pascal()],
        response: Response,
        optional_query: Annotated[str | None, Query] = None,
        optional_header: Annotated[str | None, Header] = None,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def body_json(
        self,
        name: Annotated[str, BodyJson],
        city: Annotated[str, BodyJson.custom_key("profile.address.city")],
        enabled: Annotated[bool, BodyJson.custom_name("isEnabled")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def form_auto(
        self,
        username: Annotated[str, BodyForm],
        tags: Annotated[list[str], BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo", form_encoding=BodyFormEncoding.URL_ENCODED)
    def form_urlencoded(
        self,
        first: Annotated[str, BodyForm.custom_name("first-name")],
        count: Annotated[int, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo", form_encoding=BodyFormEncoding.FORM_DATA)
    def form_multipart_fields(
        self,
        title: Annotated[str, BodyForm],
        count: Annotated[int, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()

    @post("/echo")
    def form_inferred_file(
        self,
        upload: Annotated[io.BytesIO, BodyForm],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


async def _async_call(
    backend: type, base_url: str, method_name: str, *args: Any
) -> dict[str, Any]:
    async with AsyncPipelineAPI(base_url, backend) as api:
        return await getattr(api, method_name)(*args)


def _sync_call(
    backend: type, base_url: str, method_name: str, *args: Any
) -> dict[str, Any]:
    with SyncPipelineAPI(base_url, backend) as api:
        return getattr(api, method_name)(*args)


def _header(payload: dict[str, Any], name: str) -> str | None:
    return {key.lower(): value for key, value in payload["headers"].items()}.get(
        name.lower()
    )


def _assert_components(payload: dict[str, Any]) -> None:
    assert payload["path"] == "/echo/resource-한글"
    assert payload["query"] == {
        "static_query": ["kept"],
        "basic_query": ["basic"],
        "repeated_query": ["one", "two"],
        "query-alias": ["alias"],
        "camelQuery": ["camel"],
        "PascalQuery": ["pascal"],
    }
    assert _header(payload, "X-Static") == "kept"
    assert _header(payload, "X-Custom") == "header"
    assert _header(payload, "camelHeader") == "camel-header"
    assert _header(payload, "PascalHeader") == "pascal-header"
    assert "optional_query" not in payload["query"]
    assert _header(payload, "optional_header") is None


def _assert_body_variants(
    json_payload: dict[str, Any],
    auto_form: dict[str, Any],
    urlencoded: dict[str, Any],
    multipart: dict[str, Any],
    inferred_file: dict[str, Any],
) -> None:
    assert json_payload["json"] == {
        "name": "tester",
        "profile": {"address": {"city": "Seoul"}},
        "isEnabled": True,
    }
    assert auto_form["content_type"] == "application/x-www-form-urlencoded"
    assert auto_form["form"] == {"username": ["tester"], "tags": ["one", "two"]}
    assert urlencoded["content_type"] == "application/x-www-form-urlencoded"
    assert urlencoded["form"] == {"first-name": ["tester"], "count": ["3"]}
    assert multipart["content_type"] == "multipart/form-data"
    assert multipart["form"] == {"title": ["example"], "count": ["3"]}
    assert inferred_file["files"]["upload"][0]["base64"] == base64.b64encode(
        FILE_CONTENT
    ).decode("ascii")


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_path_query_and_header_are_transmitted(
    backend: type, base_url: str
) -> None:
    payload = asyncio.run(
        _async_call(
            backend,
            base_url,
            "components",
            "resource-한글",
            "basic",
            ["one", "two"],
            "alias",
            "camel",
            "pascal",
            "header",
            "camel-header",
            "pascal-header",
        )
    )
    _assert_components(payload)


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_path_query_and_header_are_transmitted(
    backend: type, base_url: str
) -> None:
    _assert_components(
        _sync_call(
            backend,
            base_url,
            "components",
            "resource-한글",
            "basic",
            ["one", "two"],
            "alias",
            "camel",
            "pascal",
            "header",
            "camel-header",
            "pascal-header",
        )
    )


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_body_json_and_form_variants_are_transmitted(
    backend: type, base_url: str
) -> None:
    _assert_body_variants(
        asyncio.run(
            _async_call(backend, base_url, "body_json", "tester", "Seoul", True)
        ),
        asyncio.run(
            _async_call(backend, base_url, "form_auto", "tester", ["one", "two"])
        ),
        asyncio.run(_async_call(backend, base_url, "form_urlencoded", "tester", 3)),
        asyncio.run(
            _async_call(backend, base_url, "form_multipart_fields", "example", 3)
        ),
        asyncio.run(
            _async_call(
                backend, base_url, "form_inferred_file", io.BytesIO(FILE_CONTENT)
            )
        ),
    )


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_body_json_and_form_variants_are_transmitted(
    backend: type, base_url: str
) -> None:
    _assert_body_variants(
        _sync_call(backend, base_url, "body_json", "tester", "Seoul", True),
        _sync_call(backend, base_url, "form_auto", "tester", ["one", "two"]),
        _sync_call(backend, base_url, "form_urlencoded", "tester", 3),
        _sync_call(backend, base_url, "form_multipart_fields", "example", 3),
        _sync_call(backend, base_url, "form_inferred_file", io.BytesIO(FILE_CONTENT)),
    )
