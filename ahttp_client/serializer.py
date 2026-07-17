from typing import Optional

from ._types import RequestDecorator
from .request import RequestCore, AsyncRequestCore, SyncRequestCore
from .serialization.base import BaseSerializer, BaseDeserializer, ModelT


def serialize(
        model: Optional[type[ModelT]] = None,
        **serializer_kwargs,
):
    if model is None:
        model_cls = BaseSerializer.late_bind(**serializer_kwargs)
    else:
        model_cls = BaseSerializer.from_model(model, **serializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No serializer found for {model}")

    def decorator(func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore):
        if isinstance(func, RequestCore):
            if model_cls.is_late_bind:
                if func._serializer is None or func._serializer.is_late_bind:
                    raise TypeError(
                        f"Unknown serializer type. Please check body type of {func.func.__name__} method."
                    )
                func._serializer = type(func._serializer)(**model_cls._kwargs)
                func.body_parameter_type = func._serializer.body_type
                return func
            func._serializer = model_cls
            return func
        if not hasattr(func, "__extension__"):
            func.__extension__ = dict()
        func.__extension__["serializer"] = model_cls
        return func

    return decorator


def deserialize(
        model: Optional[type[ModelT]] = None,
        **deserializer_kwargs,
):
    if model is None:
        model_cls = BaseDeserializer.late_bind(**deserializer_kwargs)
    else:
        model_cls = BaseDeserializer.from_model(model, **deserializer_kwargs)

    if model_cls is None:
        raise TypeError(f"No deserializer found for {model}")

    def decorator(func: RequestDecorator[AsyncRequestCore, SyncRequestCore] | RequestCore):
        if isinstance(func, RequestCore):
            if model_cls.is_late_bind:
                if func._deserializer is None or func._deserializer.is_late_bind:
                    raise TypeError(
                        f"Unknown deserializer type. Please check return annotation of {func.func.__name__} method."
                    )
                bound_deserializer = BaseDeserializer.from_model(
                    func._deserializer._model,
                    **model_cls._kwargs,
                )
                if bound_deserializer is None:
                    raise TypeError(
                        f"Unknown deserializer type. Please check return annotation of {func.func.__name__} method."
                    )
                func._deserializer = bound_deserializer
                return func
            func._deserializer = model_cls
            return func
        if not hasattr(func, "__extension__"):
            func.__extension__ = dict()
        func.__extension__["deserializer"] = model_cls
        return func

    return decorator
