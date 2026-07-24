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

from enum import Flag, StrEnum, auto
from typing import Any


class Method(StrEnum):
    """HTTP methods accepted by request decorators and session methods."""

    CONNECT = auto()
    HEAD = auto()
    GET = auto()
    DELETE = auto()
    OPTIONS = auto()
    PATCH = auto()
    POST = auto()
    PUT = auto()
    TRACE = auto()

    def __str__(self) -> str:
        return super().__str__().upper()


class BodyType(StrEnum):
    """Encodings used for an HTTP request body."""

    JSON = "application/json"
    URL_ENCODED = "application/x-www-form-urlencoded"
    FORM_DATA = "multipart/form-data"
    RAW = auto()


class BodyFormEncoding(Flag):
    """Encoding options for parameters declared with :class:`BodyForm`.

    ``AUTO`` uses multipart form data when a file field is present and URL
    encoding otherwise.
    """

    AUTO = auto()
    URL_ENCODED = auto()
    FORM_DATA = auto()

    @property
    def body_type(self) -> BodyType:
        """Return the :class:`BodyType` represented by this form encoding.

        Raises
        ------
        ValueError
            If this value is ``AUTO`` or combines multiple encoding flags.
        """
        if self == BodyFormEncoding.URL_ENCODED:
            return BodyType.URL_ENCODED
        elif self == BodyFormEncoding.FORM_DATA:
            return BodyType.FORM_DATA
        raise ValueError(f"BodyFormEncoding.{self._name_} is not a valid body type")


class DirectResponseType(Flag):
    """Response types that can be returned directly from a request."""

    NONE = auto()
    RESPONSE = auto()
    DESERIALIZED = auto()

    def __bool__(self) -> bool:
        return self != DirectResponseType.NONE

    @classmethod
    def validate(cls, value: Any) -> None:
        """Validate that a direct-response setting selects at most one mode."""
        if isinstance(value, bool):
            return
        if not isinstance(value, cls):
            raise TypeError("directly_response must be a bool or DirectResponseType.")
        if value not in (cls.NONE, cls.RESPONSE, cls.DESERIALIZED):
            raise ValueError("Direct response modes cannot be combined.")
