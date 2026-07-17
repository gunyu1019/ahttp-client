from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar, ClassVar, Self, Optional

from ..enum import BodyType
from ..utils import is_subclass_safe, get_args_for_generic

ModelT = TypeVar("ModelT")


class BaseCodec(ABC):
    base_model_type: type[Any]

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._late_bind = False

    @staticmethod
    def is_sequence(value: Any) -> bool:
        """Return whether *value* is a collection of values to convert."""
        return isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        )

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        generic_args = get_args_for_generic(model_type)
        if generic_args is not None:
            return is_subclass_safe(generic_args, cls.base_model_type)
        return is_subclass_safe(model_type, cls.base_model_type)

    @classmethod
    def late_bind(cls, **kwargs):
        new_cls = cls()
        new_cls._kwargs = kwargs
        new_cls._late_bind = True
        return new_cls

    @property
    def is_late_bind(self) -> bool:
        return self._late_bind


class BaseSerializer(BaseCodec, ABC, Generic[ModelT]):
    """Converts models into transport-safe values."""
    _registry: ClassVar[list[type[BaseSerializer]]] = []
    body_type: ClassVar[BodyType]

    @abstractmethod
    def single_serialize(self, model: ModelT) -> Any:
        """Serialize one model."""

    def multiple_serialize(self, model: Sequence[ModelT]) -> list[Any]:
        return [
            self.single_serialize(item)
            if isinstance(item, self.base_model_type)
            else item
            for item in model
        ]

    def serialize(
        self, model: ModelT | Sequence[ModelT]
    ) -> Any | list[Any]:
        if self.is_sequence(model):
            return self.multiple_serialize(model)
        return self.single_serialize(model)

    def __init_subclass__(cls, **kwargs: Any):
        """Register a concrete backend for its configured session class."""
        super(BaseSerializer, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, "model_base_type"):
            return

        BaseSerializer._registry.append(cls)

    @classmethod
    def from_model(cls, model: type[ModelT], **kwargs) -> Optional[Self]:
        for serializer_cls in cls._registry:
            if serializer_cls.is_model_type(model):
                return serializer_cls(**kwargs)
        return None

    @classmethod
    def set_model(cls, model: type[ModelT], origin_cls: BaseCodec, **kwargs) -> Optional[Self]:
        if not origin_cls._late_bind:
            raise ValueError("Cannot set model for non-late-bound serializer")
        _kwargs = origin_cls._kwargs.copy()
        _kwargs.update(kwargs)

        for serializer_cls in cls._registry:
            if serializer_cls.is_model_type(model):
                return serializer_cls(**_kwargs)
        return None


class BaseDeserializer(BaseCodec, ABC, Generic[ModelT]):
    """Converts transport-safe values into models."""
    _registry: ClassVar[list[type[BaseDeserializer]]] = []

    def __init__(self, model: Optional[ModelT], **kwargs):
        self._model = model
        super(BaseDeserializer, self).__init__(**kwargs)

    @abstractmethod
    def single_deserialize(
        self, data: Any
    ) -> ModelT:
        """Deserialize one value into ``model_type``."""

    def multiple_deserialize(
            self, data: Sequence[Any]
    ) -> list[ModelT]:
        return [
            self.single_deserialize(item)
            if isinstance(item, self.base_model_type)
            else item
            for item in data
        ]

    def deserialize(
        self,
        data: Any | Sequence[Any],
    ) -> ModelT | list[ModelT]:
        if self.is_sequence(data):
            return self.multiple_deserialize(data)
        return self.single_deserialize(data)

    def __init_subclass__(cls, **kwargs: Any):
        """Register a concrete backend for its configured session class."""
        super(BaseDeserializer, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, "model_base_type"):
            return

        BaseDeserializer._registry.append(cls)

    @classmethod
    def from_model(cls, model: type[ModelT], **kwargs) -> Optional[Self]:
        for deserializer_cls in cls._registry:
            if deserializer_cls.is_model_type(model):
                return deserializer_cls(model, **kwargs)
        return None

    @classmethod
    def set_model(cls, model: type[ModelT], origin_cls: BaseCodec, **kwargs) -> Optional[Self]:
        if not origin_cls._late_bind:
            raise ValueError("Cannot set model for non-late-bound deserializer")
        _kwargs = origin_cls._kwargs.copy()
        _kwargs.update(kwargs)

        for deserializer_cls in cls._registry:
            if deserializer_cls.is_model_type(model):
                return deserializer_cls(model=model, **_kwargs)
        return None
