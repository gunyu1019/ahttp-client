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

Minimal serialization round-trip coverage for every HTTP backend.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import BaseModel, Field

from ahttp_client import AsyncSession, Session, post
from ahttp_client.enum import DirectResponseType
from ahttp_client.serializer import serialize
from tests.backend_integration.backend_matrix import (
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
    content_type: str
    json_body: Any = Field(alias="json")


@dataclass
class DataclassRequestItem:
    name: str
    optional: str | None = None
    occurred_at: datetime = datetime(2026, 7, 18, tzinfo=timezone.utc)


@dataclass
class DataclassEchoPayload:
    content_type: str
    json: Any


class AsyncSerializationAPI(AsyncSession):
    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    @serialize(exclude_none=True)
    async def round_trip(
        self,
        payload: dict[str, list[RequestItem]],
    ) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    async def dataclass_round_trip(
        self,
        payload: dict[str, list[DataclassRequestItem]],
    ) -> DataclassEchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")


class SyncSerializationAPI(Session):
    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    @serialize(exclude_none=True)
    def round_trip(
        self,
        payload: dict[str, list[RequestItem]],
    ) -> EchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")

    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    def dataclass_round_trip(
        self,
        payload: dict[str, list[DataclassRequestItem]],
    ) -> DataclassEchoPayload:
        raise AssertionError("direct deserialization must skip the endpoint body")


def _request_payload() -> dict[str, list[RequestItem]]:
    return {
        "items": [
            RequestItem(name="first"),
            RequestItem(name="second", optional="value"),
        ]
    }


def _dataclass_request_payload() -> dict[str, list[DataclassRequestItem]]:
    return {
        "items": [
            DataclassRequestItem(name="first"),
            DataclassRequestItem(name="second", optional="value"),
        ]
    }


def _assert_round_trip(payload: EchoPayload) -> None:
    assert isinstance(payload, EchoPayload)
    assert payload.content_type == "application/json"
    assert payload.json_body == {
        "items": [
            {
                "name": "first",
                "occurred_at": "2026-07-18T00:00:00Z",
            },
            {
                "name": "second",
                "optional": "value",
                "occurred_at": "2026-07-18T00:00:00Z",
            },
        ]
    }


def _assert_dataclass_round_trip(payload: DataclassEchoPayload) -> None:
    assert isinstance(payload, DataclassEchoPayload)
    assert payload.content_type == "application/json"
    assert payload.json == {
        "items": [
            {
                "name": "first",
                "optional": None,
                "occurred_at": "2026-07-18T00:00:00+00:00",
            },
            {
                "name": "second",
                "optional": "value",
                "occurred_at": "2026-07-18T00:00:00+00:00",
            },
        ]
    }


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_serialization_round_trip(backend: type, base_url: str) -> None:
    async def run() -> tuple[EchoPayload, DataclassEchoPayload]:
        async with AsyncSerializationAPI(base_url, backend) as api:
            pydantic_payload = await api.round_trip(_request_payload())
            dataclass_payload = await api.dataclass_round_trip(
                _dataclass_request_payload()
            )
            return pydantic_payload, dataclass_payload

    pydantic_payload, dataclass_payload = asyncio.run(run())
    _assert_round_trip(pydantic_payload)
    _assert_dataclass_round_trip(dataclass_payload)


@pytest.mark.backend_integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_serialization_round_trip(backend: type, base_url: str) -> None:
    with SyncSerializationAPI(base_url, backend) as api:
        pydantic_payload = api.round_trip(_request_payload())
        dataclass_payload = api.dataclass_round_trip(_dataclass_request_payload())

    _assert_round_trip(pydantic_payload)
    _assert_dataclass_round_trip(dataclass_payload)
