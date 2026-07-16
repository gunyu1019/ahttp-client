from __future__ import annotations

from typing import Any, Optional, Callable

from pydantic import BaseModel, IncEx
from pydantic.config import ExtraValues

from .base import BaseDeserializer, BaseSerializer


class PydanticSerializer(BaseSerializer[BaseModel]):
    """Serialize Pydantic models with :meth:`BaseModel.model_dump`."""
    model_base_type: type[BaseModel] = BaseModel

    def __init__(self,
                 include: Optional[IncEx] = None,
                 exclude: Optional[IncEx] = None,
                 by_alias: Optional[bool] = None,
                 exclude_unset: bool = False,
                 exclude_defaults: bool = False,
                 exclude_none: bool = False,
                 exclude_computed_fields: bool = False,
                 context: Optional[Any] = None,
                 fallback: Optional[Callable[[Any], Any]] = None
                 ):
        self.include = include
        self.exclude = exclude
        self.by_alias = by_alias
        self.exclude_unset = exclude_unset
        self.exclude_defaults = exclude_defaults
        self.exclude_none = exclude_none
        self.exclude_computed_fields = exclude_computed_fields
        self.context = context
        self.fallback = fallback
        super().__init__()

    def single_serialize(self, model: BaseModel) -> dict[str, Any]:
        return model.model_dump(
            include=self.include,
            exclude=self.exclude,
            by_alias=self.by_alias,
            exclude_unset=self.exclude_unset,
            exclude_defaults=self.exclude_defaults,
            exclude_none=self.exclude_none,
            exclude_computed_fields=self.exclude_computed_fields,
            context=self.context,
            fallback=self.fallback
        )


class PydanticDeserializer(BaseDeserializer[BaseModel]):
    """Deserialize values with :meth:`BaseModel.model_validate`."""
    model_base_type: type[BaseModel] = BaseModel

    def __init__(self,
                 strict: Optional[bool] = None,
                 extra: Optional[ExtraValues] = None,
                 context: Optional[Any] = None,
                 by_alias: Optional[bool] = None,
                 by_name: Optional[bool] = None,
                 ):
        self.strict = strict
        self.extra = extra
        self.context = context
        self.by_alias = by_alias
        self.by_name = by_name
        super().__init__()

    def single_deserialize(
            self, model_type: type[BaseModel], data: Any
    ) -> BaseModel:
        return model_type.model_validate(
            data,
            extra=self.extra,
            strict=self.strict,
            context=self.context,
            by_alias=self.by_alias,
            by_name=self.by_name
        )
