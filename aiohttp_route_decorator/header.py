from .kv_core import KVcore
from typing import TypeVar, Generic

T = TypeVar('T')


class Header(Generic[T], KVcore[str, T]):
    def __init__(self, key: str, value: T):
        super().__init__(key, value)

    def __repr__(self):
        return f"<Header {self.__str__()}>"
