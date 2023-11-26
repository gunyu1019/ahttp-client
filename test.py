import sys
from typing import Union, NewType


class NewType3:
    """NewType creates simple unique types with almost zero runtime overhead.

    NewType(name, tp) is considered a subtype of tp
    by static type checkers. At runtime, NewType(name, tp) returns
    a dummy callable that simply returns its argument. Usage::

        UserId = NewType('UserId', int)

        def name_by_id(user_id: UserId) -> str:
            ...

        UserId('user')          # Fails type check

        name_by_id(42)          # Fails type check
        name_by_id(UserId(42))  # OK

        num = UserId(5) + 1     # type: int
    """

    __call__ = lambda _, x: x

    def __init__(self, name, tp):
        self.__qualname__ = name
        if '.' in name:
            name = name.rpartition('.')[-1]
        self.__name__ = name
        self.__supertype__ = tp
        def_mod = sys._getframe(2).f_globals.get('__name__', '__main__')
        if def_mod != 'typing':
            self.__module__ = def_mod

    def __mro_entries__(self, bases):
        # We defined __mro_entries__ to get a better error message
        # if a user attempts to subclass a NewType instance. bpo-46170
        superclass_name = self.__name__

        class Dummy:
            def __init_subclass__(cls):
                subclass_name = cls.__name__
                raise TypeError(
                    f"Cannot subclass an instance of NewType. Perhaps you were looking for: "
                    f"`{subclass_name} = NewType({subclass_name!r}, {superclass_name})`"
                )

        return (Dummy,)

    def __repr__(self):
        return f'{self.__module__}.{self.__qualname__}'

    def __reduce__(self):
        return self.__qualname__

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]


B = NewType3("name", int)
C = NewType("name", int)


def p3(s: B):
    print(s)


p3(10)
p3("str")



def p4(s: C):
    print(s)


p4(10)
p4("str")

