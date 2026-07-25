"""aiohttp integration coverage for Pydantic request and response codecs."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

pytest.importorskip("pydantic")

import aiohttp
from pydantic import BaseModel, ConfigDict, Field

from ahttp_client import AsyncSession, post
from ahttp_client.enum import DirectResponseType
from ahttp_client.serializer import deserialize, serialize


class PydanticProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    display_name: str = Field(alias="displayName")
    email: str | None = None
    created_at: datetime


class PydanticEchoModel(BaseModel):
    content_type: str
    json_body: Any = Field(alias="json")


class AiohttpPydanticAPI(AsyncSession):
    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    @serialize(by_alias=True, exclude_none=True)
    @deserialize(PydanticEchoModel)
    async def round_trip(
        self,
        payload: dict[str, list[PydanticProfile]],
    ) -> PydanticEchoModel:
        raise AssertionError("direct response mode must deserialize the response")


@pytest.mark.serialization_integration
def test_pydantic_serializes_and_deserializes_with_aiohttp(base_url: str) -> None:
    async def run() -> PydanticEchoModel:
        payload = {
            "profiles": [
                PydanticProfile(
                    user_id=7,
                    display_name="first",
                    created_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
                ),
                PydanticProfile(
                    user_id=8,
                    display_name="second",
                    email="second@example.com",
                    created_at=datetime(2026, 7, 26, tzinfo=timezone.utc),
                ),
            ]
        }
        async with AiohttpPydanticAPI(base_url, aiohttp.ClientSession) as api:
            return await api.round_trip(payload)

    response = asyncio.run(run())

    assert isinstance(response, PydanticEchoModel)
    assert response.content_type == "application/json"
    assert response.json_body == {
        "profiles": [
            {
                "userId": 7,
                "displayName": "first",
                "created_at": "2026-07-25T00:00:00Z",
            },
            {
                "userId": 8,
                "displayName": "second",
                "email": "second@example.com",
                "created_at": "2026-07-26T00:00:00Z",
            },
        ]
    }
