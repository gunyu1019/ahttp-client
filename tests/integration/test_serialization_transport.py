"""Serializer/deserializer behavior across every concrete HTTP backend."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import BaseModel, Field

from ahttp_client import AsyncSession, Response, Session, post
from ahttp_client.serializer import deserialize, serialize
from tests.integration.backend_matrix import (
    ASYNC_BACKEND_IDS,
    ASYNC_BACKENDS,
    SYNC_BACKEND_IDS,
    SYNC_BACKENDS,
)


class RequestItem(BaseModel):
    name: str
    optional: str | None = None
    occurred_at: datetime = datetime(2026, 7, 18, tzinfo=timezone.utc)


class EchoPayload(BaseModel):
    method: str
    path: str
    content_type: str
    json_body: Any = Field(default=None, alias="json")


class AsyncSerializationAPI(AsyncSession):
    @post("/echo", body_parameter="item", directly_response=True)
    @serialize(exclude_none=True)
    @deserialize(EchoPayload)
    async def direct_model(self, item: RequestItem) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post("/echo", body_parameter="items", directly_response=True)
    @deserialize(EchoPayload)
    async def generic_body(self, items: list[RequestItem]) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post("/echo", body_parameter="item")
    @serialize(exclude_none=True)
    @deserialize(EchoPayload)
    async def response_model(
        self,
        item: RequestItem,
        response: Response,
    ) -> EchoPayload:
        return response.model

    @post("/echo", directly_response=True)
    @deserialize(EchoPayload)
    async def transformed_response(self) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")


@AsyncSerializationAPI.transformed_response.after_hook
async def _async_extract_json(session, response: Response) -> dict[str, Any]:
    return response.json()


class SyncSerializationAPI(Session):
    @post("/echo", body_parameter="item", directly_response=True)
    @serialize(exclude_none=True)
    @deserialize(EchoPayload)
    def direct_model(self, item: RequestItem) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post("/echo", body_parameter="items", directly_response=True)
    @deserialize(EchoPayload)
    def generic_body(self, items: list[RequestItem]) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post("/echo", body_parameter="item")
    @serialize(exclude_none=True)
    @deserialize(EchoPayload)
    def response_model(
        self,
        item: RequestItem,
        response: Response,
    ) -> EchoPayload:
        return response.model

    @post("/echo", directly_response=True)
    @deserialize(EchoPayload)
    def transformed_response(self) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")


@SyncSerializationAPI.transformed_response.after_hook
def _sync_extract_json(session, response: Response) -> dict[str, Any]:
    return response.json()


def _assert_direct_model(payload: EchoPayload) -> None:
    assert isinstance(payload, EchoPayload)
    assert payload.content_type == "application/json"
    assert payload.json_body == {
        "name": "single",
        "occurred_at": "2026-07-18T00:00:00Z",
    }


def _assert_generic_body(payload: EchoPayload) -> None:
    assert isinstance(payload, EchoPayload)
    assert payload.content_type == "application/json"
    assert payload.json_body == [
        {
            "name": "first",
            "optional": None,
            "occurred_at": "2026-07-18T00:00:00Z",
        },
        {
            "name": "second",
            "optional": "value",
            "occurred_at": "2026-07-18T00:00:00Z",
        },
    ]


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_serialization_round_trip_for_every_backend(
    backend: type,
    base_url: str,
) -> None:
    async def run() -> tuple[EchoPayload, EchoPayload, EchoPayload, EchoPayload]:
        async with AsyncSerializationAPI(base_url, backend) as api:
            direct = await api.direct_model(RequestItem(name="single"))
            generic = await api.generic_body([
                RequestItem(name="first"),
                RequestItem(name="second", optional="value"),
            ])
            response_model = await api.response_model(RequestItem(name="single"))
            transformed = await api.transformed_response()
            return direct, generic, response_model, transformed

    direct, generic, response_model, transformed = asyncio.run(run())

    _assert_direct_model(direct)
    _assert_generic_body(generic)
    _assert_direct_model(response_model)
    assert transformed.method == "POST"
    assert transformed.path == "/echo"


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_serialization_round_trip_for_every_backend(
    backend: type,
    base_url: str,
) -> None:
    with SyncSerializationAPI(base_url, backend) as api:
        direct = api.direct_model(RequestItem(name="single"))
        generic = api.generic_body([
            RequestItem(name="first"),
            RequestItem(name="second", optional="value"),
        ])
        response_model = api.response_model(RequestItem(name="single"))
        transformed = api.transformed_response()

    _assert_direct_model(direct)
    _assert_generic_body(generic)
    _assert_direct_model(response_model)
    assert transformed.method == "POST"
    assert transformed.path == "/echo"
