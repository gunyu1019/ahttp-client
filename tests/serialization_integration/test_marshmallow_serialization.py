"""aiohttp integration coverage for Marshmallow request and response codecs."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

pytest.importorskip("marshmallow")

import aiohttp
from marshmallow import Schema, fields

from ahttp_client import AsyncSession, post
from ahttp_client.enum import DirectResponseType
from ahttp_client.serializer import deserialize, serialize


class MarshmallowProfileSchema(Schema):
    user_id = fields.Int(data_key="userId", required=True)
    display_name = fields.Str(data_key="displayName", required=True)
    email = fields.Email(allow_none=True)
    created_at = fields.DateTime(required=True)


class MarshmallowEchoSchema(Schema):
    content_type = fields.Str(required=True)
    json_body = fields.Raw(data_key="json", required=True)


class AiohttpMarshmallowAPI(AsyncSession):
    @post(
        "/echo",
        body_parameter="payload",
        directly_response=DirectResponseType.DESERIALIZED,
    )
    @serialize(MarshmallowProfileSchema, schema=MarshmallowProfileSchema(), many=True)
    @deserialize(
        MarshmallowEchoSchema,
        schema=MarshmallowEchoSchema(),
        unknown="exclude",
    )
    async def round_trip(
        self,
        payload: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise AssertionError("direct response mode must deserialize the response")


@pytest.mark.serialization_integration
def test_marshmallow_serializes_and_deserializes_with_aiohttp(base_url: str) -> None:
    async def run() -> dict[str, Any]:
        payload = [
            {
                "user_id": 17,
                "display_name": "marshmallow",
                "email": None,
                "created_at": datetime(2026, 7, 25, tzinfo=timezone.utc),
                "ignored": "not in the schema",
            }
        ]
        async with AiohttpMarshmallowAPI(base_url, aiohttp.ClientSession) as api:
            return await api.round_trip(payload)

    response = asyncio.run(run())

    assert response == {
        "content_type": "application/json",
        "json_body": [
            {
                "userId": 17,
                "displayName": "marshmallow",
                "email": None,
                "created_at": "2026-07-25T00:00:00+00:00",
            }
        ],
    }
