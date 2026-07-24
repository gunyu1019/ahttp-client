"""MIT License

Copyright (c) 2023-present gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import AbstractSet, Any, Literal, Optional, cast, get_args

from marshmallow import Schema

from .base import BaseDeserializer, BaseSerializer
from ..enum import BodyType
from ..response import Response
from ..utils import is_annotated_parameter, is_subclass_safe


class _MarshmallowCodec:
    """Shared schema construction for Marshmallow codecs."""

    base_model_type: type[Schema] = Schema

    @staticmethod
    def _schema_type(model_type: Any) -> Optional[type[Schema]]:
        """Return a schema class from a direct or ``Annotated`` annotation."""
        if is_subclass_safe(model_type, Schema):
            return cast(type[Schema], model_type)
        if is_annotated_parameter(model_type):
            return _MarshmallowCodec._schema_type(get_args(model_type)[0])
        return None

    def _initialize_schema(
        self,
        schema: Schema,
    ) -> None:
        if not isinstance(schema, Schema):
            raise TypeError("Expected an instance of marshmallow.Schema for schema, " f"got {type(schema).__name__}")

        self.schema = schema

    @classmethod
    def is_model_type(cls, model_type: type[Any]) -> bool:
        """Return whether an annotation directly identifies a schema."""
        return cls._schema_type(model_type) is not None


class MarshmallowSerializer(_MarshmallowCodec, BaseSerializer[Any]):
    """Serialize request bodies with :meth:`marshmallow.Schema.dump`.

    A schema instance is required; it determines the complete-body conversion
    independently of the annotated domain-model type.
    """

    body_type = BodyType.JSON

    def __init__(
        self,
        *,
        schema: Schema,
        many: Optional[bool] = None,
    ):
        self._initialize_schema(schema)
        self.many = many
        super().__init__()

    def single_serialize(self, model: Any) -> Any:
        """Delegate serialization to the configured Marshmallow schema."""
        return self.schema.dump(model, many=self.many)

    def serialize(self, model: Any) -> Any:
        """Dump the complete body once, including ``many=True`` collections."""
        return self.single_serialize(model)

    def multiple_serialize(self, model: Sequence[Any]) -> Any:
        """Dump a collection once so Marshmallow can apply ``many=True``."""
        return self.single_serialize(model)


class MarshmallowDeserializer(_MarshmallowCodec, BaseDeserializer[Any]):
    """Deserialize JSON response bodies with :meth:`marshmallow.Schema.load`.

    A schema instance is required; its ``load`` implementation determines the
    deserialized value independently of the return annotation.
    """

    def __init__(
        self,
        model: Any = None,
        *,
        schema: Schema,
        many: Optional[bool] = None,
        partial: Optional[bool | Sequence[str] | AbstractSet[str]] = None,
        unknown: Optional[Literal["exclude", "include", "raise"]] = None,
    ):
        self._initialize_schema(schema)
        self.many = many
        self.partial = partial
        self.unknown = unknown
        super().__init__(model=model)

    def get_data(self, response: Response) -> Any:
        """Parse a response body as the schema's input value."""
        return response.json()

    def single_deserialize(self, data: Any) -> Any:
        """Delegate deserialization and validation to the Marshmallow schema."""
        return self.schema.load(
            data,
            many=self.many,
            partial=self.partial,
            unknown=self.unknown,
        )

    def deserialize(self, data: Any) -> Any:
        """Load the complete response once, including ``many=True`` collections."""
        return self.single_deserialize(data)

    def multiple_deserialize(self, data: Sequence[Any]) -> Any:
        """Load a collection once so Marshmallow can apply ``many=True``."""
        return self.single_deserialize(data)
