from enum import StrEnum, auto


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
