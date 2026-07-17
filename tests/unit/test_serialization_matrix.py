from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Any

import pytest
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
    field_serializer,
    field_validator,
)

from ahttp_client import Body, BodyType, Response, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.serialization import (
    BaseCodec,
    BaseDeserializer,
    BaseSerializer,
    PydanticDeserializer,
    PydanticSerializer,
)
from ahttp_client.serializer import deserialize, serialize


class Item(BaseModel):
    name: str
    optional: str | None = None


class OptionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    identifier: int = Field(alias="id")
    label: str = "default"
    optional: str | None = None
    occurred_at: datetime = datetime(2026, 7, 18, tzinfo=timezone.utc)

    @computed_field
    @property
    def summary(self) -> str:
        return f"{self.identifier}:{self.label}"


class ContextModel(BaseModel):
    value: str

    @field_validator("value")
    @classmethod
    def prefix_value(cls, value: str, info):
        return f"{(info.context or {}).get('prefix', '')}{value}"

    @field_serializer("value")
    def suffix_value(self, value: str, info):
        return f"{value}{(info.context or {}).get('suffix', '')}"


class ArbitraryPayload:
    pass


class ArbitraryModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: ArbitraryPayload


@dataclass
class PlainModel:
    value: str


class PlainSerializer(BaseSerializer[PlainModel]):
    base_model_type = PlainModel
    body_type = BodyType.JSON

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        super().__init__()

    def single_serialize(self, model: PlainModel) -> dict[str, str]:
        return {"value": f"{self.prefix}{model.value}"}


class PlainDeserializer(BaseDeserializer[PlainModel]):
    base_model_type = PlainModel

    def __init__(self, model: type[PlainModel], prefix: str = ""):
        self.prefix = prefix
        super().__init__(model)

    def single_deserialize(self, data: Any) -> PlainModel:
        return self._model(f"{self.prefix}{data['value']}")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([1, 2], True),
        ((1, 2), True),
        (range(2), True),
        ("text", False),
        (b"bytes", False),
        (bytearray(b"bytes"), False),
        ({1, 2}, False),
        ({"key": "value"}, False),
        ((item for item in range(2)), False),
    ],
)
def test_sequence_detection_contract(value: Any, expected: bool) -> None:
    assert BaseCodec.is_sequence(value) is expected


@pytest.mark.parametrize(
    "model_type",
    [
        Item,
        Item | None,
        list[Item],
        tuple[Item, ...],
        dict[str, Item],
    ],
)
def test_registry_resolves_supported_pydantic_annotations(model_type: Any) -> None:
    assert isinstance(BaseSerializer.from_model(model_type), PydanticSerializer)
    assert isinstance(BaseDeserializer.from_model(model_type), PydanticDeserializer)


@pytest.mark.parametrize("model_type", [int, str, list[int], dict[str, int]])
def test_registry_rejects_annotations_without_registered_models(model_type: Any) -> None:
    assert BaseSerializer.from_model(model_type) is None
    assert BaseDeserializer.from_model(model_type) is None


def test_custom_codec_registration_factory_and_late_options() -> None:
    serializer = BaseSerializer.from_model(PlainModel, prefix="out-")
    deserializer = BaseDeserializer.from_model(PlainModel, prefix="in-")

    assert isinstance(serializer, PlainSerializer)
    assert isinstance(deserializer, PlainDeserializer)
    assert serializer.serialize(PlainModel("value")) == {"value": "out-value"}
    assert deserializer.deserialize({"value": "value"}) == PlainModel("in-value")

    late_serializer = BaseSerializer.late_bind(prefix="late-")
    late_deserializer = BaseDeserializer.late_bind(prefix="late-")
    bound_serializer = BaseSerializer.set_model(PlainModel, late_serializer)
    bound_deserializer = BaseDeserializer.set_model(PlainModel, late_deserializer)

    assert bound_serializer.serialize(PlainModel("value")) == {"value": "late-value"}
    assert bound_deserializer.deserialize({"value": "value"}) == PlainModel("late-value")


def test_set_model_rejects_an_already_bound_codec() -> None:
    serializer = BaseSerializer.from_model(Item)
    deserializer = BaseDeserializer.from_model(Item)

    with pytest.raises(ValueError, match="non-late-bound serializer"):
        BaseSerializer.set_model(Item, serializer)
    with pytest.raises(ValueError, match="non-late-bound deserializer"):
        BaseDeserializer.set_model(Item, deserializer)


@pytest.mark.parametrize(
    ("serializer", "expected"),
    [
        (PydanticSerializer(include={"identifier"}), {"identifier": 1}),
        (PydanticSerializer(exclude={"optional", "summary"}), {
            "identifier": 1,
            "label": "default",
            "occurred_at": "2026-07-18T00:00:00Z",
        }),
        (PydanticSerializer(by_alias=True, exclude={"summary"}), {
            "id": 1,
            "label": "default",
            "optional": None,
            "occurred_at": "2026-07-18T00:00:00Z",
        }),
        (PydanticSerializer(exclude_none=True, exclude={"summary"}), {
            "identifier": 1,
            "label": "default",
            "occurred_at": "2026-07-18T00:00:00Z",
        }),
        (PydanticSerializer(exclude_defaults=True, exclude={"summary"}), {
            "identifier": 1,
        }),
        (PydanticSerializer(exclude_computed_fields=True), {
            "identifier": 1,
            "label": "default",
            "optional": None,
            "occurred_at": "2026-07-18T00:00:00Z",
        }),
    ],
)
def test_pydantic_serializer_option_matrix(
    serializer: PydanticSerializer,
    expected: dict[str, Any],
) -> None:
    assert serializer.serialize(OptionModel(identifier=1)) == expected


def test_pydantic_serializer_exclude_unset_context_and_fallback() -> None:
    assert PydanticSerializer(exclude_unset=True).serialize(
        OptionModel(identifier=1)
    ) == {"identifier": 1, "summary": "1:default"}

    context_model = ContextModel.model_validate(
        {"value": "value"},
        context={"prefix": "in-"},
    )
    assert PydanticSerializer(context={"suffix": "-out"}).serialize(
        context_model
    ) == {"value": "in-value-out"}

    arbitrary = ArbitraryModel(payload=ArbitraryPayload())
    assert PydanticSerializer(fallback=lambda _: "fallback").serialize(arbitrary) == {
        "payload": "fallback"
    }


def test_pydantic_serializer_nested_mapping_and_sequence() -> None:
    serializer = PydanticSerializer(exclude_none=True)

    assert serializer.serialize(
        {
            "single": Item(name="one"),
            "many": [Item(name="two"), Item(name="three")],
        }
    ) == {
        "single": {"name": "one"},
        "many": [{"name": "two"}, {"name": "three"}],
    }


def test_pydantic_deserializer_option_and_error_matrix() -> None:
    with pytest.raises(ValidationError):
        PydanticDeserializer(OptionModel, strict=True).deserialize({"id": "1"})

    with pytest.raises(ValidationError):
        PydanticDeserializer(OptionModel, extra="forbid").deserialize(
            {"id": 1, "unexpected": True}
        )

    assert PydanticDeserializer(OptionModel, by_alias=True, by_name=False).deserialize(
        {"id": 1}
    ).identifier == 1
    assert PydanticDeserializer(OptionModel, by_alias=False, by_name=True).deserialize(
        {"identifier": 1}
    ).identifier == 1
    assert PydanticDeserializer(
        ContextModel,
        context={"prefix": "in-"},
    ).deserialize({"value": "value"}) == ContextModel(value="in-value")


@pytest.mark.parametrize(
    ("model_type", "data", "expected"),
    [
        (Item, {"name": "one"}, Item(name="one")),
        (Item, [{"name": "one"}], [Item(name="one")]),
        (list[Item], [{"name": "one"}], [Item(name="one")]),
        (tuple[Item, ...], [{"name": "one"}], (Item(name="one"),)),
        (dict[str, Item], {"one": {"name": "one"}}, {"one": Item(name="one")}),
        (Item | None, None, None),
        (Item | None, {"name": "one"}, Item(name="one")),
    ],
)
def test_pydantic_deserializer_shape_matrix(
    model_type: Any,
    data: Any,
    expected: Any,
) -> None:
    deserializer = BaseDeserializer.from_model(model_type)

    assert deserializer is not None
    assert deserializer.deserialize(data) == expected


def test_serializer_decorators_reject_unknown_models_and_annotations() -> None:
    class Unknown:
        pass

    with pytest.raises(TypeError, match="No serializer found"):
        serialize(Unknown)
    with pytest.raises(TypeError, match="No deserializer found"):
        deserialize(Unknown)

    with pytest.raises(TypeError, match="Unknown serializer type"):
        @request("POST", "/", body_parameter="value")
        @serialize()
        def serialize_endpoint(session, value: Unknown):
            pass

    with pytest.raises(TypeError, match="Unknown deserializer type"):
        @request("GET", "/", directly_response=True)
        @deserialize()
        def deserialize_endpoint(session) -> Unknown:
            pass


def test_optional_and_annotated_body_serialization() -> None:
    @request("POST", "/")
    @serialize(exclude_none=True)
    def endpoint(session, item: Annotated[Item | None, Body]):
        pass

    item_request = endpoint.copy()
    item_request._fill_parameter(object(), {"item": Item(name="item")})
    assert item_request.body == {"name": "item"}

    empty_request = endpoint.copy()
    empty_request._fill_parameter(object(), {"item": None})
    assert empty_request.body is None


class FakeResponse(Response):
    def __init__(self, payload: Any, *, asynchronous: bool = False):
        self.payload = payload
        self._closed = False
        self.asynchronous = asynchronous

    @property
    def closed(self) -> bool:
        return self._closed

    def json(self):
        return self.payload

    def close(self) -> None:
        self._closed = True

    async def async_close(self) -> None:
        self._closed = True


def test_response_model_with_and_without_deserializer() -> None:
    response = FakeResponse({"name": "item"})
    response._deserializer = None
    assert response.model is None

    response._deserializer = PydanticDeserializer(Item)
    assert response.model == Item(name="item")


@pytest.mark.parametrize("payload", [{"name": "item"}, {"invalid": True}])
def test_sync_direct_deserialization_closes_on_success_and_failure(payload: Any) -> None:
    class FakeSession:
        directly_response = False

        def __init__(self):
            self.response = FakeResponse(payload)

        def _make_request(self, request_obj, path):
            return self.response

    @request("GET", "/", directly_response=True)
    @deserialize(Item)
    def endpoint(session):
        raise AssertionError("direct response must skip endpoint body")

    session = FakeSession()
    if "name" in payload:
        assert endpoint._execute(session) == Item(name="item")
    else:
        with pytest.raises(ValidationError):
            endpoint._execute(session)
    assert session.response.closed is True


@pytest.mark.parametrize("payload", [{"name": "item"}, {"invalid": True}])
def test_async_direct_deserialization_closes_on_success_and_failure(payload: Any) -> None:
    class FakeSession:
        directly_response = False

        def __init__(self):
            self.response = FakeResponse(payload, asynchronous=True)

        async def _make_request(self, request_obj, path):
            return self.response

    @request("GET", "/", directly_response=True)
    @deserialize(Item)
    async def endpoint(session):
        raise AssertionError("direct response must skip endpoint body")

    session = FakeSession()
    if "name" in payload:
        assert asyncio.run(endpoint._execute(session)) == Item(name="item")
    else:
        with pytest.raises(ValidationError):
            asyncio.run(endpoint._execute(session))
    assert session.response.closed is True


@pytest.mark.xfail(
    strict=True,
    reason="explicit DESERIALIZED mode does not infer a codec from the return annotation",
)
def test_direct_response_type_deserialized_uses_return_annotation() -> None:
    @request("GET", "/", directly_response=DirectResponseType.DESERIALIZED)
    def endpoint(session) -> Item:
        pass

    assert isinstance(endpoint._deserializer, PydanticDeserializer)


@pytest.mark.xfail(
    strict=True,
    reason="registry model detection only inspects the first generic level",
)
def test_nested_generic_registry_resolution() -> None:
    annotation = list[dict[str, Item | None]]

    assert isinstance(BaseSerializer.from_model(annotation), PydanticSerializer)
    deserializer = BaseDeserializer.from_model(annotation)
    assert isinstance(deserializer, PydanticDeserializer)
    assert deserializer.deserialize([{"item": {"name": "value"}, "none": None}]) == [
        {"item": Item(name="value"), "none": None}
    ]
