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
