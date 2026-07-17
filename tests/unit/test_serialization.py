from __future__ import annotations

from ahttp_client.serialization import PydanticDeserializer, PydanticSerializer
from pydantic import BaseModel, field_serializer, field_validator


class Item(BaseModel):
    name: str
    optional: str | None = None

    @field_validator("name")
    @classmethod
    def prefix_from_context(cls, value: str, info):
        prefix = info.context.get("prefix", "") if info.context else ""
        return f"{prefix}{value}"

    @field_serializer("name")
    def suffix_from_context(self, value: str, info):
        suffix = info.context.get("suffix", "") if info.context else ""
        return f"{value}{suffix}"


def test_pydantic_codecs_apply_directional_options() -> None:
    context = {"prefix": "in-", "suffix": "-out"}
    deserializer = PydanticDeserializer(
        Item,
        context=context,
        strict=True,
    )
    serializer = PydanticSerializer(
        context=context,
        exclude_none=True,
    )

    item = deserializer.deserialize({"name": "widget"})

    assert item == Item(name="in-widget")
    assert serializer.serialize(item) == {"name": "in-widget-out"}


def test_pydantic_serializer_preserves_none_by_default() -> None:
    serializer = PydanticSerializer()

    assert serializer.serialize(Item(name="item")) == {
        "name": "item",
        "optional": None,
    }
