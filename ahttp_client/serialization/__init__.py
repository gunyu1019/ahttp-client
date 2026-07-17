from .base import BaseCodec, BaseSerializer, BaseDeserializer

__all__ = ["BaseCodec", "BaseSerializer", "BaseDeserializer"]

try:
    from .pydantic import PydanticSerializer, PydanticDeserializer
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
else:
    __all__ += ["PydanticSerializer", "PydanticDeserializer"]
