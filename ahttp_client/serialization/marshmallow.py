"""Marshmallow codecs backed directly by :class:`marshmallow.Schema`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self, Optional, get_args

from marshmallow import Schema

from .base import BaseDeserializer, BaseSerializer
from ..enum import BodyType
from ..response import Response
from ..utils import is_annotated_parameter, is_subclass_safe


class _MarshmallowCodec:
    """Shared schema construction for Marshmallow codecs."""

    base_model_type: type[Schema] = Schema

    @staticmethod
    def _schema_type(model_type: Any) -> type[Optional[Schema]]:
        """Return a schema class from a direct or ``Annotated`` annotation."""
        if is_subclass_safe(model_type, Schema):
            return model_type
        if is_annotated_parameter(model_type):
            return _MarshmallowCodec._schema_type(get_args(model_type)[0])
        return None

    def _initialize_schema(
        self,
        model: Any,
        schema: Optional[Schema],
        schema_kwargs: dict[str, Any],
    ) -> None:
        schema_type = self._schema_type(model)
        if schema_type is None:
            raise TypeError(f"No Marshmallow schema found in {model!r}")
        if schema is not None and not isinstance(schema, schema_type):
            raise TypeError(
                f"Expected an instance of {schema_type.__name__} for schema, "
                f"got {type(schema).__name__}"
            )
        if schema is not None and schema_kwargs:
            raise TypeError(
                "Schema options cannot be combined with an existing schema instance"
            )

        self.schema = schema or schema_type(**schema_kwargs)

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        """Return whether an annotation directly identifies a schema."""
        return cls._schema_type(model_type) is not None


class MarshmallowSerializer(_MarshmallowCodec, BaseSerializer[Any]):
    """Serialize request bodies with :meth:`marshmallow.Schema.dump`."""

    body_type = BodyType.JSON

    def __init__(
        self,
        model: Any,
        *,
        schema: Optional[Schema] = None,
        **schema_kwargs: Any,
    ):
        self._initialize_schema(model, schema, schema_kwargs)
        super().__init__()

    @classmethod
    def _from_model(cls, model: Any, **kwargs: Any) -> Self:
        return cls(model, **kwargs)

    def single_serialize(self, model: Any) -> Any:
        """Delegate serialization to the configured Marshmallow schema."""
        return self.schema.dump(model)

    def serialize(self, model: Any) -> Any:
        """Dump the complete body once, including ``many=True`` collections."""
        return self.single_serialize(model)

    def multiple_serialize(self, model: Sequence[Any]) -> Any:
        """Dump a collection once so Marshmallow can apply ``many=True``."""
        return self.single_serialize(model)


class MarshmallowDeserializer(_MarshmallowCodec, BaseDeserializer[Any]):
    """Deserialize JSON response bodies with :meth:`marshmallow.Schema.load`."""

    def __init__(
        self,
        model: Any,
        *,
        schema: Optional[Schema] = None,
        **schema_kwargs: Any,
    ):
        self._initialize_schema(model, schema, schema_kwargs)
        super().__init__(model=model)

    def get_data(self, response: Response) -> Any:
        """Parse a response body as the schema's input value."""
        return response.json()

    def single_deserialize(self, data: Any) -> Any:
        """Delegate deserialization and validation to the Marshmallow schema."""
        return self.schema.load(data)

    def deserialize(self, data: Any) -> Any:
        """Load the complete response once, including ``many=True`` collections."""
        return self.single_deserialize(data)

    def multiple_deserialize(self, data: Sequence[Any]) -> Any:
        """Load a collection once so Marshmallow can apply ``many=True``."""
        return self.single_deserialize(data)
