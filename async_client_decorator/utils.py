from collections.abc import Collection
from types import UnionType
from typing import Annotated, get_origin


def is_subclass_safe(_class, _class_info) -> bool:
    """
    Same functionality as `issubclass` method
    However, _class parameter can be list of type.
    """
    if not isinstance(_class, Collection):
        _class = (_class,)
    return any([issubclass(t, _class_info) for t in _class if isinstance(t, type)])


def separate_union_type(t):
    """
    If type is Union, return list of type
    else return t
    """
    if isinstance(t, UnionType):
        return t.__args__
    return t


def is_annotated_parameter(t) -> bool:
    """
    Return `True` if type is Annotated
    """
    return get_origin(t) is Annotated
