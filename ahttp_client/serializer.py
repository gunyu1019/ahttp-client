from typing import Optional

from ._types import RequestDecorator
from .request import RequestCore, AsyncRequestCore, SyncRequestCore
from .serialization.base import BaseSerializer, BaseDeserializer, ModelT


def serialize(
        model: Optional[ModelT] = None,
        **serializer_kwargs,
):
    model_cls = BaseSerializer.from_model(model, **serializer_kwargs)
    if model is None and len(serializer_kwargs) > 0:
        model_cls = BaseSerializer.late_bind(**serializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No serializer found for {model}")

    def decorator(func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore):
        if isinstance(func, RequestCore):
            func._serializer = model_cls
            return func
        if not hasattr(func, "__extension__"):
            func.__extension__ = dict()
        func.__extension__["serializer"] = model_cls
        return func

    return decorator


def deserialize(
        model: Optional[ModelT] = None,
        **deserializer_kwargs,
):
    model_cls = BaseDeserializer.from_model(model, **deserializer_kwargs)
    if model is None and len(deserializer_kwargs) > 0:
        model_cls = BaseDeserializer.late_bind(**deserializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No deserializer found for {model}")

    def decorator(func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore):
        if isinstance(func, RequestCore):
            func._deserializer = model_cls
            return func
        if not hasattr(func, "__extension__"):
            func.__extension__ = dict()
        func.__extension__["deserializer"] = model_cls
        return func

    return decorator
