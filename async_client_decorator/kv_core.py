from typing import Generic, TypeVar

KT = TypeVar('KT')
VT = TypeVar('VT')


class KVcore(Generic[KT, VT]):
    def __init__(self, key: KT, value: VT):
        self.key: KT = key
        self.value: VT = value

    def __str__(self):
        return f"{self.key}:{str(self.value)}"

    def __eq__(self, other):
        if isinstance(other, KVcore):
            return self.key == other.key and self.value == other.value
        return self.value == other
