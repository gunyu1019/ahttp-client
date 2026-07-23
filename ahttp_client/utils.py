from collections.abc import Collection
from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin


def is_subclass_safe(_class: Any, _class_info: Any) -> bool:
    """
    Same functionality as `issubclass` method
    However, _class parameter can be list of type.
    """
    _class = make_collection(_class)
    return any([issubclass(t, _class_info) for t in _class if isinstance(t, type)])


def separate_union_type(t: Any) -> Any:
    """Return union members for ``Union`` and ``|`` annotations, else *t*."""
    if isinstance(t, UnionType) or get_origin(t) in (Union, UnionType):
        return get_args(t)
    return t


def is_annotated_parameter(t: Any) -> bool:
    """
    Return `True` if type is Annotated
    """
    return get_origin(t) is Annotated


def get_origin_for_generic(t: Any) -> Any:
    """Return a generic annotation's origin, or *t* when it has no origin."""
    return get_origin(t) or t


def get_args_for_generic(t: Any) -> tuple[Any, ...] | None:
    """
    If type is Generic, return argument of generic type
    else return t
    """
    args = get_args(t)
    if len(args) == 0:
        return None
    return args


def make_collection(t: Any) -> Collection[Any]:
    # ``Enum`` classes and other class objects can satisfy ``Collection``
    # through their metaclass, but still represent one type for callers such
    # as ``is_subclass_safe``.
    if isinstance(t, type) or not isinstance(t, Collection):
        return (t,)
    return t
