from collections.abc import Collection
from types import UnionType, GenericAlias
from typing import Annotated, get_origin


def is_subclass_safe(_class, _class_info) -> bool:
    """
    Same functionality as `issubclass` method
    However, _class parameter can be list of type.
    """
    _class = make_collection(_class)
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


def get_origin_for_generic(t):
    """
    If type is Generic, return origin of generic type
    else return t
    """
    if isinstance(t, GenericAlias):
        return t.__origin__
    return t


def make_collection(t):
    if not isinstance(t, Collection):
        return (t,)
    return t
