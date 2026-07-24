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

from typing import Any, Optional, Protocol, Unpack, cast, overload

from ._types import RequestDecorator
from .request import RequestCore, AsyncRequestCore, SyncRequestCore
from .serialization.base import BaseCodec, BaseSerializer, BaseDeserializer, ModelT
from .serialization._types import (
    DataclassDeserializeOptions,
    DataclassSerializeOptions,
    MarshmallowDeserializeOptions,
    MarshmallowSerializeOptions,
    PydanticDeserializeOptions,
    PydanticSerializeOptions,
)


class _ExtensionOwner(Protocol):
    """Callable request decorator carrying deferred request extensions."""

    __extension__: dict[str, Any]


@overload
def serialize(
    model: Optional[type[ModelT]] = None,
    **serializer_kwargs: Unpack[PydanticSerializeOptions],
) -> RequestDecorator[Any, Any]: ...


@overload
def serialize(
    model: Optional[type[ModelT]] = None,
    **serializer_kwargs: Unpack[DataclassSerializeOptions],
) -> RequestDecorator[Any, Any]: ...


@overload
def serialize(
    model: Optional[type[ModelT]] = None,
    **serializer_kwargs: Unpack[MarshmallowSerializeOptions],
) -> RequestDecorator[Any, Any]: ...


def serialize(
    model: Optional[type[ModelT]] = None,
    **serializer_kwargs: Any,
) -> RequestDecorator[Any, Any]:
    """Decorate a request to serialize its complete body.

    When ``model`` is empty, the serializer is selected from the complete body
    parameter annotation. Serializer keyword arguments are applied after the
    model type is resolved.

    Parameters
    ----------
    model: Optional[type[ModelT]]
        Model type used to select a registered serializer.
    **serializer_kwargs
        Keyword arguments forwarded to the serializer constructor.

    Raises
    ------
    TypeError
        If no serializer is registered for the model type.
    """
    model_cls: Optional[BaseCodec]
    if model is None:
        model_cls = BaseSerializer.late_bind(**serializer_kwargs)
    else:
        model_cls = BaseSerializer.from_model(model, **serializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No serializer found for {model}")

    def decorator(
        func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore[Any, Any],
    ) -> Any:
        if isinstance(func, RequestCore):
            func._bind_serializer(model_cls)
            return func
        extension_owner = cast(_ExtensionOwner, func)
        if not hasattr(extension_owner, "__extension__"):
            extension_owner.__extension__ = {}
        extension_owner.__extension__["serializer"] = model_cls
        return func

    return cast(RequestDecorator[Any, Any], decorator)


@overload
def deserialize(
    model: Optional[type[ModelT]] = None,
    **deserializer_kwargs: Unpack[PydanticDeserializeOptions],
) -> RequestDecorator[Any, Any]: ...


@overload
def deserialize(
    model: Optional[type[ModelT]] = None,
    **deserializer_kwargs: Unpack[DataclassDeserializeOptions],
) -> RequestDecorator[Any, Any]: ...


@overload
def deserialize(
    model: Optional[type[ModelT]] = None,
    **deserializer_kwargs: Unpack[MarshmallowDeserializeOptions],
) -> RequestDecorator[Any, Any]: ...


def deserialize(
    model: Optional[type[ModelT]] = None,
    **deserializer_kwargs: Any,
) -> RequestDecorator[Any, Any]:
    """Decorate a request to deserialize its HTTP response.

    When ``model`` is empty, the deserializer is selected from the return
    annotation. Deserializer keyword arguments are applied after the model type
    is resolved.

    Parameters
    ----------
    model: Optional[type[ModelT]]
        Model type used to select a registered deserializer.
    **deserializer_kwargs
        Keyword arguments forwarded to the deserializer constructor.

    Raises
    ------
    TypeError
        If no deserializer is registered for the model type.
    """
    model_cls: Optional[BaseCodec]
    if model is None:
        model_cls = BaseDeserializer.late_bind(**deserializer_kwargs)
    else:
        model_cls = BaseDeserializer.from_model(model, **deserializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No deserializer found for {model}")

    def decorator(
        func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore[Any, Any],
    ) -> Any:
        if isinstance(func, RequestCore):
            func._bind_deserializer(model_cls)
            return func
        extension_owner = cast(_ExtensionOwner, func)
        if not hasattr(extension_owner, "__extension__"):
            extension_owner.__extension__ = {}
        extension_owner.__extension__["deserializer"] = model_cls
        return func

    return cast(RequestDecorator[Any, Any], decorator)
