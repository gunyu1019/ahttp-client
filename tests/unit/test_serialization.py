from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ahttp_client import BodyType, Response, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.serialization import BaseDeserializer, BaseSerializer
from ahttp_client.serializer import deserialize, serialize


@dataclass
class Model:
    value: str


class ModelSerializer(BaseSerializer[Model]):
    base_model_type = Model
    body_type = BodyType.JSON

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        super().__init__()

    def single_serialize(self, model: Model) -> dict[str, str]:
        return {"value": f"{self.prefix}{model.value}"}


class ModelDeserializer(BaseDeserializer[Model]):
    base_model_type = Model

    def __init__(self, model: type[Model], prefix: str = ""):
        self.prefix = prefix
        super().__init__(model)

    def single_deserialize(self, data: Any) -> Model:
        return self._model(f"{self.prefix}{data['value']}")

    def get_data(self, response: Response) -> Any:
        return response.payload


def test_registered_codecs_convert_single_and_multiple_values() -> None:
    serializer = BaseSerializer.from_model(Model, prefix="serialized-")
    deserializer = BaseDeserializer.from_model(Model, prefix="deserialized-")

    assert isinstance(serializer, ModelSerializer)
    assert isinstance(deserializer, ModelDeserializer)
    assert serializer.serialize(Model("one")) == {"value": "serialized-one"}
    assert serializer.serialize([Model("one"), Model("two")]) == [
        {"value": "serialized-one"},
        {"value": "serialized-two"},
    ]
    assert deserializer.deserialize({"value": "one"}) == Model("deserialized-one")
    assert deserializer.deserialize([{"value": "one"}, {"value": "two"}]) == [
        Model("deserialized-one"),
        Model("deserialized-two"),
    ]


def test_registry_and_late_binding_resolve_nested_model_annotations() -> None:
    annotation = list[dict[str, Model | None]]

    assert isinstance(BaseSerializer.from_model(annotation), ModelSerializer)
    assert isinstance(BaseDeserializer.from_model(annotation), ModelDeserializer)

    serializer = BaseSerializer.set_model(
        Model,
        BaseSerializer.late_bind(prefix="late-"),
    )
    deserializer = BaseDeserializer.set_model(
        Model,
        BaseDeserializer.late_bind(prefix="late-"),
    )

    assert serializer.serialize(Model("value")) == {"value": "late-value"}
    assert deserializer.deserialize({"value": "value"}) == Model("late-value")


def test_request_decorators_bind_serialization_from_annotations() -> None:
    @request("POST", "/", body_parameter="model")
    @serialize(prefix="request-")
    def serialize_endpoint(session, model: Model):
        pass

    @request("GET", "/", directly_response=True)
    @deserialize(prefix="response-")
    def deserialize_endpoint(session) -> Model:
        pass

    serialize_endpoint._fill_parameter(object(), {"model": Model("value")})

    assert serialize_endpoint.body == {"value": "request-value"}
    assert serialize_endpoint.body_type is BodyType.JSON
    assert deserialize_endpoint.directly_response is DirectResponseType.DESERIALIZED
    assert isinstance(deserialize_endpoint._deserializer, ModelDeserializer)
    assert deserialize_endpoint._deserializer.prefix == "response-"


def test_explicit_deserialized_mode_and_response_model_use_registered_codec() -> None:
    @request("GET", "/", directly_response=DirectResponseType.DESERIALIZED)
    def endpoint(session) -> Model:
        pass

    assert isinstance(endpoint._deserializer, ModelDeserializer)

    response = Response.__new__(Response)
    response.payload = {"value": "model"}
    response._deserializer = endpoint._deserializer

    assert response.model == Model("model")
