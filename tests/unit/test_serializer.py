from pydantic import BaseModel

from ahttp_client import BodyType, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.serialization import PydanticDeserializer, PydanticSerializer
from ahttp_client.serializer import deserialize, serialize


class Item(BaseModel):
    name: str
    optional: str | None = None


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
