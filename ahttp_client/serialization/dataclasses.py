from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    get_type_hints,
    Callable,
    Optional,
)
from uuid import UUID

from .base import BaseDeserializer, BaseSerializer
from ..enum import BodyType
from ..response import Response
from ..utils import (
    get_args_for_generic,
    get_origin_for_generic,
    is_annotated_parameter,
    is_subclass_safe,
    separate_union_type,
)

_UNTYPED_CONTAINER_TYPES = (
    Mapping,
    Sequence,
    dict,
    list,
    tuple,
    set,
    frozenset,
)


def _is_untyped_container(model_type: Any) -> bool:
    """Return whether *model_type* is a container without item annotations."""
    return get_origin_for_generic(model_type) in _UNTYPED_CONTAINER_TYPES and get_args_for_generic(model_type) is None


class DataclassesSerializer(BaseSerializer[Any]):
    """Serialize dataclass instances and nested containers."""

    # ``base_model_type`` is required for codec registration. Model detection
    # itself is implemented with ``is_dataclass`` below.
    base_model_type: type[Any] = type
    body_type = BodyType.JSON

    def __init__(
        self,
        deserialize_date: Optional[Callable[[date], str]] = None,
        deserialize_time: Optional[Callable[[time], str]] = None,
        deserialize_datetime: Optional[Callable[[datetime], str]] = None,
        deserialize_other: Optional[Callable[[Any], str]] = None,
    ):
        self.deserialize_date = deserialize_date or (lambda x: x.isoformat())
        self.deserialize_time = deserialize_time or (lambda x: x.isoformat())
        self.deserialize_datetime = deserialize_datetime or (lambda x: x.isoformat())
        self.deserialize_other = deserialize_other or (lambda x: str(x))
        super().__init__()

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        """Return whether an annotation contains the configured model type."""
        if _is_untyped_container(model_type):
            return True
        if isinstance(model_type, type) and is_dataclass(model_type):
            return True
        generic_args = get_args_for_generic(model_type)
        if generic_args is None:
            return False
        return any(cls.is_model_type(arg) for arg in generic_args)

    def single_serialize(self, model: Any) -> Any:
        """Serialize one dataclass value into JSON-compatible containers."""
        if is_dataclass(model) and not isinstance(model, type):
            return {field.name: self.single_serialize(getattr(model, field.name)) for field in fields(model)}
        if isinstance(model, Mapping):
            return {key: self.single_serialize(value) for key, value in model.items()}
        if isinstance(model, (set, frozenset, tuple, list)):
            return [self.single_serialize(item) for item in model]
        if isinstance(model, Enum):
            return self.single_serialize(model.value)
        if isinstance(model, datetime):
            return self.deserialize_datetime(model)
        if isinstance(model, date):
            return self.deserialize_date(model)
        if isinstance(model, time):
            return self.deserialize_time(model)
        if isinstance(model, (Decimal, UUID)):
            return model.__str__()
        if isinstance(model, (str, int, float, bool, type(None))):
            return model
        return self.deserialize_other(model)

    def multiple_serialize(self, model: Sequence[Any]) -> list[Any]:
        return [self.single_serialize(item) for item in model]


class DataclassesDeserializer(BaseDeserializer[Any]):
    """Reconstruct dataclass instances from JSON-compatible values."""

    def get_data(self, response: Response) -> Any:
        """Parse a response body as deserializer input."""
        return response.json()

    base_model_type: type[Any] = type

    def __init__(
        self,
        model: Any,
        serialize_date: Optional[Callable[[type[Any], Any], date]] = None,
        serialize_time: Optional[Callable[[type[Any], Any], time]] = None,
        serialize_datetime: Optional[Callable[[type[Any], Any], datetime]] = None,
        serialize_other: Optional[Callable[[type, Any], Any]] = None,
    ):
        super().__init__(model=model)
        self.serialize_date = serialize_date or (lambda _, x: date.fromisoformat(x))
        self.serialize_time = serialize_time or (lambda _, x: time.fromisoformat(x))
        self.serialize_datetime = serialize_datetime or (lambda _, x: datetime.fromisoformat(x))
        self.serialize_uuid = lambda cls, x: cls(x)
        self.serialize_decimal = lambda _, x: Decimal(str(x))

        self.serialize_other = serialize_other or (lambda _, x: x)

        self.serializes = (
            dict,
            Mapping,
            frozenset,
            set,
            tuple,
            list,
            Sequence,
            Enum,
            datetime,
            date,
            time,
            UUID,
            Decimal,
        )

    def serialize_enum(self, model: type[Any], data: Any) -> Any:
        """Convert an enum value when *model* is an enum subclass."""
        if not is_subclass_safe(model, Enum):
            return self.serialize_other(model, data)
        if isinstance(data, model):
            return data
        return model(data)

    def serialize_mapping(self, model: type[Any], data: Any) -> Any:
        generic_args = get_args_for_generic(model)
        if generic_args is None:
            return data
        key_type, value_type = generic_args
        return {
            self._deserialize_model(key_type, key): self._deserialize_model(value_type, value)
            for key, value in data.items()
        }

    def serialize_dict(self, model: type[Any], data: Any) -> Any:
        """Deserialize a ``dict`` annotation using mapping semantics."""
        return self.serialize_mapping(model, data)

    def serialize_tuple(self, model: type[Any], data: Any) -> Any:
        item_types = get_args_for_generic(model)
        if item_types is None:
            return tuple(data)
        if len(item_types) == 2 and item_types[1] is Ellipsis:
            return tuple(self._deserialize_model(item_types[0], item) for item in data)
        return tuple(self._deserialize_model(item_type, item) for item_type, item in zip(item_types, data))

    def serialize_frozenset(self, model: type[Any], data: Any) -> Any:
        return self.serialize_set(model, data)

    def serialize_set(self, model: type[Any], data: Any) -> Any:
        generic_args = get_args_for_generic(model)
        collection_type = get_origin_for_generic(model)
        if generic_args is None:
            return collection_type(data)
        (item_type,) = generic_args
        return collection_type(self._deserialize_model(item_type, item) for item in data)

    def serialize_list(self, model: type[Any], data: Any) -> Any:
        generic_args = get_args_for_generic(model)
        if generic_args is None:
            return data
        (item_type,) = generic_args
        return [self._deserialize_model(item_type, item) for item in data]

    def serialize_sequence(self, model: type[Any], data: Any) -> Any:
        """Deserialize a ``Sequence`` annotation as a JSON-compatible list."""
        return self.serialize_list(model, data)

    def _serialize_special_type(self, model: type[Any], data: Any) -> Any:
        origin = get_origin_for_generic(model)
        for cls in self.serializes:
            if not is_subclass_safe(origin, cls):
                continue

            if isinstance(model, type) and isinstance(data, model):
                return data
            serializer = getattr(self, f"serialize_{cls.__name__.lower()}")
            return serializer(model, data)
        return self.serialize_other(model, data)

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        """Return whether an annotation contains the configured model type."""
        if _is_untyped_container(model_type):
            return True
        if isinstance(model_type, type) and is_dataclass(model_type):
            return True
        generic_args = get_args_for_generic(model_type)
        if generic_args is None:
            return False
        return any(cls.is_model_type(arg) for arg in generic_args)

    def _deserialize_model(self, model: Any, data: Any) -> Any:
        if data is None:
            return None

        if is_annotated_parameter(model):
            annotated_args = get_args_for_generic(model)
            assert annotated_args is not None
            model = annotated_args[0]

        separated_model = separate_union_type(model)
        if isinstance(separated_model, tuple):
            model_types = [item for item in separated_model if item is not type(None)]
            if len(model_types) == 1:
                return self._deserialize_model(model_types[0], data)

            # Standard dataclasses do not validate scalar union members. When
            # a union contains a dataclass, however, a JSON object can still be
            # reconstructed deterministically.
            if isinstance(data, Mapping):
                for model_type in model_types:
                    if isinstance(model_type, type) and is_dataclass(model_type):
                        return self._deserialize_model(model_type, data)
            return data

        if isinstance(model, type) and is_dataclass(model):
            if not isinstance(data, Mapping):
                raise TypeError(f"Expected a mapping to deserialize {model.__name__}, " f"got {type(data).__name__}")

            hints = get_type_hints(model)
            kwargs: dict[str, Any] = {}
            for field in fields(model):
                if not field.init or field.name not in data:
                    continue
                field_type = hints.get(field.name, field.type)
                kwargs[field.name] = self._deserialize_model(
                    field_type,
                    data[field.name],
                )
            return model(**kwargs)

        return self._serialize_special_type(model, data)

    def single_deserialize(self, data: Any) -> Any:
        """Deserialize one value against the configured model annotation."""
        return self._deserialize_model(self._model, data)

    def deserialize(self, data: Any) -> Any:
        """Deserialize data while preserving collection model annotations."""
        if (
            self.is_sequence(data)
            and get_origin_for_generic(self._model) is self._model
            and not _is_untyped_container(self._model)
        ):
            return self.multiple_deserialize(data)
        return self.single_deserialize(data)
