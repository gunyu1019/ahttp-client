from .base import BaseCodec, BaseSerializer, BaseDeserializer
from .dataclasses import DataclassesDeserializer, DataclassesSerializer

__all__ = [
    "BaseCodec",
    "BaseSerializer",
    "BaseDeserializer",
    "DataclassesSerializer",
    "DataclassesDeserializer",
]

try:
    from .pydantic import PydanticSerializer, PydanticDeserializer
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
else:
    __all__ += ["PydanticSerializer", "PydanticDeserializer"]

try:
    from .marshmallow import MarshmallowSerializer, MarshmallowDeserializer
except ModuleNotFoundError as exc:
    if exc.name != "marshmallow":
        raise
else:
    __all__ += ["MarshmallowSerializer", "MarshmallowDeserializer"]
