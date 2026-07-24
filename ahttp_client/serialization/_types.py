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

Dependency-free type definitions for built-in serialization codecs.
"""

from __future__ import annotations

from datetime import date, datetime, time
from collections.abc import Sequence
from typing import AbstractSet, Any, Callable, Literal, NotRequired, Optional, Protocol, TypedDict


class PydanticSerializeOptions(TypedDict, total=False):
    """Keyword arguments supported by the Pydantic request serializer.

    ``include`` and ``exclude`` use ``Any`` because Pydantic's recursive
    ``IncEx`` type is not part of the core package's public dependency surface.
    """

    include: Any
    exclude: Any
    by_alias: bool | None
    exclude_unset: bool
    exclude_defaults: bool
    exclude_none: bool
    exclude_computed_fields: bool
    context: Any
    fallback: Callable[[Any], Any] | None


class PydanticDeserializeOptions(TypedDict, total=False):
    """Keyword arguments supported by the Pydantic response deserializer."""

    strict: bool | None
    extra: Literal["allow", "ignore", "forbid"] | None
    context: Any
    by_alias: bool | None
    by_name: bool | None


class DataclassSerializeOptions(TypedDict, total=False):
    """Keyword arguments supported by the dataclass request serializer."""

    deserialize_date: Callable[[date], str] | None
    deserialize_time: Callable[[time], str] | None
    deserialize_datetime: Callable[[datetime], str] | None
    deserialize_other: Callable[[Any], str] | None


class DataclassDeserializeOptions(TypedDict, total=False):
    """Keyword arguments supported by the dataclass response deserializer."""

    serialize_date: Callable[[type[Any], Any], date] | None
    serialize_time: Callable[[type[Any], Any], time] | None
    serialize_datetime: Callable[[type[Any], Any], datetime] | None
    serialize_other: Callable[[type[Any], Any], Any] | None


class MarshmallowDumpSchema(Protocol):
    """Dependency-free structural type for a Marshmallow dump schema."""

    def dump(self, obj: Any, *, many: Optional[bool] = None) -> Any: ...


class MarshmallowLoadSchema(Protocol):
    """Dependency-free structural type for a Marshmallow load schema."""

    def load(
        self,
        data: Any,
        *,
        many: Optional[bool] = None,
        partial: Optional[bool | Sequence[str] | AbstractSet[str]] = None,
        unknown: Optional[Literal["exclude", "include", "raise"]] = None,
    ) -> Any: ...


class MarshmallowSerializeOptions(TypedDict):
    """Keyword arguments supported by the Marshmallow request serializer."""

    schema: MarshmallowDumpSchema
    many: NotRequired[Optional[bool]]


class MarshmallowDeserializeOptions(TypedDict):
    """Keyword arguments supported by the Marshmallow response deserializer."""

    schema: MarshmallowLoadSchema
    many: NotRequired[Optional[bool]]
    partial: NotRequired[Optional[bool | Sequence[str] | AbstractSet[str]]]
    unknown: NotRequired[Optional[Literal["exclude", "include", "raise"]]]
