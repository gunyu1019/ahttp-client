from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar, ClassVar, Optional

from ..enum import BodyType
from ..response import Response
from ..utils import is_subclass_safe, get_args_for_generic

ModelT = TypeVar("ModelT")


class BaseCodec(ABC):
    """Base class for codecs that resolve model-specific implementations."""

    base_model_type: type[Any]

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._late_bind = False

    @staticmethod
    def is_sequence(value: Any) -> bool:
        """Return whether *value* is a collection of values to convert."""
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        """Return whether an annotation contains the configured model type."""
        if is_subclass_safe(model_type, cls.base_model_type):
            return True
        generic_args = get_args_for_generic(model_type)
        if generic_args is None:
            return False
        return any(cls.is_model_type(arg) for arg in generic_args)

    @classmethod
    def late_bind(cls, **kwargs: Any) -> BaseCodec:
        """Return a placeholder that stores options until a model type is known."""
        return _LateBoundCodec(**kwargs)

    @property
    def is_late_bind(self) -> bool:
        """Return whether this codec is waiting for a model type."""
        return self._late_bind


class _LateBoundCodec(BaseCodec):
    """Store codec options until a concrete model backend is known."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._late_bind = True


class BaseSerializer(BaseCodec, ABC, Generic[ModelT]):
    """Base codec that converts models into transport-safe values."""

    _registry: ClassVar[list[type[BaseSerializer[Any]]]] = []
    body_type: ClassVar[BodyType]

    @abstractmethod
    def single_serialize(self, model: ModelT) -> Any:
        """Serialize one model."""

    def multiple_serialize(self, model: Sequence[ModelT]) -> list[Any]:
        """Serialize a sequence of models."""
        return [self._serialize_value(item) for item in model]

    def _serialize_value(self, value: Any) -> Any:
        """Recursively convert registered models inside JSON containers."""
        if isinstance(value, self.base_model_type):
            return self.single_serialize(value)
        if isinstance(value, Mapping):
            return {key: self._serialize_value(item) for key, item in value.items()}
        if self.is_sequence(value):
            return [self._serialize_value(item) for item in value]
        return value

    def serialize(self, model: ModelT | Sequence[ModelT]) -> Any | list[Any]:
        """Serialize one model or a sequence of models."""
        return self._serialize_value(model)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register a serializer for its configured model type."""
        super(BaseSerializer, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, "base_model_type"):
            return

        BaseSerializer._registry.append(cls)

    @classmethod
    def from_model(cls, model: type[ModelT], **kwargs: Any) -> Optional[BaseSerializer[ModelT]]:
        """Return the serializer registered for a model annotation, if any."""
        # User-defined codecs are registered after built-in fallback codecs
        # such as the dataclasses codec, and therefore take precedence.
        for serializer_cls in reversed(cls._registry):
            if serializer_cls.is_model_type(model):
                return serializer_cls(**kwargs)
        return None

    @classmethod
    def set_model(
        cls,
        model: type[ModelT],
        origin_cls: BaseCodec,
        **kwargs: Any,
    ) -> Optional[BaseSerializer[ModelT]]:
        """Resolve a late-bound serializer for a model annotation.

        Keyword arguments override options stored by ``origin_cls``.

        Raises
        ------
        ValueError
            If ``origin_cls`` is not late-bound.
        """
        if not origin_cls._late_bind:
            raise ValueError("Cannot set model for non-late-bound serializer")
        _kwargs = origin_cls._kwargs.copy()
        _kwargs.update(kwargs)

        for serializer_cls in reversed(cls._registry):
            if serializer_cls.is_model_type(model):
                return serializer_cls(**_kwargs)
        return None


class BaseDeserializer(BaseCodec, ABC, Generic[ModelT]):
    """Base codec that converts transport-safe values into models."""

    _registry: ClassVar[list[type[BaseDeserializer[Any]]]] = []

    def __init__(self, model: Optional[ModelT], **kwargs: Any) -> None:
        self._model = model
        super(BaseDeserializer, self).__init__(**kwargs)

    @abstractmethod
    def single_deserialize(self, data: Any) -> ModelT:
        """Deserialize one value into a model."""

    def get_data(self, response: Response) -> Any:
        """Extract deserializer input from a response.

        Custom deserializers that consume the response object directly can
        rely on this identity implementation.
        """
        return response

    def multiple_deserialize(self, data: Sequence[Any]) -> list[ModelT]:
        """Deserialize a sequence of values into models."""
        return [self.single_deserialize(item) for item in data]

    def deserialize(
        self,
        data: Any | Sequence[Any],
    ) -> ModelT | list[ModelT]:
        """Deserialize one value or a sequence of values."""
        if self.is_sequence(data):
            return self.multiple_deserialize(data)
        return self.single_deserialize(data)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register a deserializer for its configured model type."""
        super(BaseDeserializer, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, "base_model_type"):
            return

        BaseDeserializer._registry.append(cls)

    @classmethod
    def from_model(cls, model: type[ModelT], **kwargs: Any) -> Optional[BaseDeserializer[ModelT]]:
        """Return the deserializer registered for a model annotation, if any."""
        # User-defined codecs are registered after built-in fallback codecs
        # such as the dataclasses codec, and therefore take precedence.
        for deserializer_cls in reversed(cls._registry):
            if deserializer_cls.is_model_type(model):
                return deserializer_cls(model, **kwargs)
        return None

    @classmethod
    def set_model(
        cls,
        model: type[ModelT],
        origin_cls: BaseCodec,
        **kwargs: Any,
    ) -> Optional[BaseDeserializer[ModelT]]:
        """Resolve a late-bound deserializer for a model annotation.

        Keyword arguments override options stored by ``origin_cls``.

        Raises
        ------
        ValueError
            If ``origin_cls`` is not late-bound.
        """
        if not origin_cls._late_bind:
            raise ValueError("Cannot set model for non-late-bound deserializer")
        _kwargs = origin_cls._kwargs.copy()
        _kwargs.update(kwargs)

        for deserializer_cls in reversed(cls._registry):
            if deserializer_cls.is_model_type(model):
                return deserializer_cls(model=model, **_kwargs)
        return None
