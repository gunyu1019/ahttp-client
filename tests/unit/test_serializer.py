import asyncio
from datetime import datetime, timezone

from pydantic import BaseModel

from ahttp_client import BodyType, Response, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.serialization import (
    BaseDeserializer,
    PydanticDeserializer,
    PydanticSerializer,
)
from ahttp_client.serializer import deserialize, serialize


class Item(BaseModel):
    name: str
    optional: str | None = None


class Event(BaseModel):
    occurred_at: datetime


def test_late_bound_serializer_uses_body_annotation_and_options() -> None:
    @request("POST", "/", body_parameter="item")
    @serialize(exclude_none=True)
    def endpoint(session, item: Item):
        pass

    assert isinstance(endpoint._serializer, PydanticSerializer)
    assert endpoint.body_type is BodyType.JSON

    endpoint._fill_parameter(object(), {"item": Item(name="item")})

    assert endpoint.body == {"name": "item"}


def test_late_bound_deserializer_uses_return_annotation_and_options() -> None:
    @request("GET", "/", directly_response=True)
    @deserialize(strict=True)
    def endpoint(session) -> Item:
        pass

    assert endpoint.directly_response is DirectResponseType.DESERIALIZED
    assert isinstance(endpoint._deserializer, PydanticDeserializer)
    assert endpoint._deserializer.strict is True


def test_late_binding_allows_empty_options() -> None:
    @request("POST", "/", body_parameter="item")
    @serialize()
    def serialize_endpoint(session, item: Item):
        pass

    @request("GET", "/", directly_response=True)
    @deserialize()
    def deserialize_endpoint(session) -> Item:
        pass

    assert isinstance(serialize_endpoint._serializer, PydanticSerializer)
    assert isinstance(deserialize_endpoint._deserializer, PydanticDeserializer)


def test_late_binding_supports_both_decorator_orders() -> None:
    @serialize(exclude_none=True)
    @request("POST", "/", body_parameter="item")
    def serialize_endpoint(session, item: Item):
        pass

    @deserialize(strict=True)
    @request("GET", "/", directly_response=True)
    def deserialize_endpoint(session) -> Item:
        pass

    serialize_endpoint._fill_parameter(object(), {"item": Item(name="item")})

    assert serialize_endpoint.body == {"name": "item"}
    assert isinstance(deserialize_endpoint._deserializer, PydanticDeserializer)
    assert deserialize_endpoint._deserializer.strict is True


def test_deserializer_converts_each_item_for_a_model_sequence() -> None:
    deserializer = PydanticDeserializer(Item)

    result = deserializer.deserialize([{"name": "first"}, {"name": "second"}])

    assert result == [Item(name="first"), Item(name="second")]


def test_deserializer_validates_generic_model_annotations() -> None:
    list_deserializer = BaseDeserializer.from_model(list[Item])
    dict_deserializer = BaseDeserializer.from_model(dict[str, Item])

    assert list_deserializer is not None
    assert dict_deserializer is not None
    assert list_deserializer.deserialize([{"name": "first"}]) == [
        Item(name="first")
    ]
    assert dict_deserializer.deserialize({"first": {"name": "item"}}) == {
        "first": Item(name="item")
    }


def test_pydantic_serializer_returns_json_safe_values() -> None:
    serializer = PydanticSerializer()

    result = serializer.serialize(
        Event(occurred_at=datetime(2026, 7, 18, tzinfo=timezone.utc))
    )

    assert result == {"occurred_at": "2026-07-18T00:00:00Z"}


def test_deserializer_accepts_data_transformed_by_after_hook() -> None:
    class FakeResponse(Response):
        def __init__(self):
            self._closed = False

        @property
        def closed(self) -> bool:
            return self._closed

        def json(self):
            return {"name": "hooked"}

        def close(self) -> None:
            self._closed = True

    class FakeSession:
        directly_response = False

        def __init__(self):
            self.response = FakeResponse()

        def _make_request(self, request_obj, path):
            return self.response

    @request("GET", "/", directly_response=True)
    @deserialize(Item)
    def endpoint(session):
        raise AssertionError("direct response must skip the endpoint body")

    @endpoint.after_hook
    def extract_json(session, response):
        return response.json()

    session = FakeSession()

    assert endpoint._execute(session) == Item(name="hooked")
    assert session.response.closed is True


def test_async_deserializer_accepts_data_transformed_by_after_hook() -> None:
    class FakeResponse(Response):
        def __init__(self):
            self._closed = False

        @property
        def closed(self) -> bool:
            return self._closed

        def json(self):
            return {"name": "hooked"}

        async def async_close(self) -> None:
            self._closed = True

    class FakeSession:
        directly_response = False

        def __init__(self):
            self.response = FakeResponse()

        async def _make_request(self, request_obj, path):
            return self.response

    @request("GET", "/", directly_response=True)
    @deserialize(Item)
    async def endpoint(session):
        raise AssertionError("direct response must skip the endpoint body")

    @endpoint.after_hook
    async def extract_json(session, response):
        return response.json()

    session = FakeSession()

    assert asyncio.run(endpoint._execute(session)) == Item(name="hooked")
    assert session.response.closed is True
