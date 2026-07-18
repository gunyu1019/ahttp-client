from typing import Optional

from ._types import RequestDecorator
from .request import RequestCore, AsyncRequestCore, SyncRequestCore
from .serialization.base import BaseSerializer, BaseDeserializer, ModelT


def serialize(
        model: Optional[type[ModelT]] = None,
        **serializer_kwargs,
):
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
    if model is None:
        model_cls = BaseSerializer.late_bind(**serializer_kwargs)
    else:
        model_cls = BaseSerializer.from_model(model, **serializer_kwargs)

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
        model: Optional[type[ModelT]] = None,
        **deserializer_kwargs,
):
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
    if model is None:
        model_cls = BaseDeserializer.late_bind(**deserializer_kwargs)
    else:
        model_cls = BaseDeserializer.from_model(model, **deserializer_kwargs)

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
