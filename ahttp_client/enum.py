from typing import overload
from enum import Flag, StrEnum, auto


class Method(StrEnum):
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
    JSON = "application/json"
    URL_ENCODED = "application/x-www-form-urlencoded"
    FORM_DATA = "multipart/form-data"
    RAW = auto()


class BodyFormEncoding(Flag):
    AUTO = auto()
    URL_ENCODED = auto()
    FORM_DATA = auto()

    @property
    def body_type(self) -> BodyType:
        if self == BodyFormEncoding.URL_ENCODED:
            return BodyType.URL_ENCODED
        elif self == BodyFormEncoding.FORM_DATA:
            return BodyType.FORM_DATA
        raise ValueError(f"BodyFormEncoding.{self._name_} is not a valid body type")