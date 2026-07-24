from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Callable

from pydantic.main import BaseModel, IncEx
from pydantic.config import ExtraValues
from pydantic import TypeAdapter

from .base import BaseDeserializer, BaseSerializer
from ..response import Response
from ..enum import BodyType


class PydanticSerializer(BaseSerializer[BaseModel]):
    """Serialize Pydantic models with :meth:`BaseModel.model_dump`."""

    base_model_type: type[BaseModel] = BaseModel
    body_type = BodyType.JSON

    def __init__(
        self,
        include: Optional[IncEx] = None,
        exclude: Optional[IncEx] = None,
        by_alias: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_computed_fields: bool = False,
        context: Optional[Any] = None,
        fallback: Optional[Callable[[Any], Any]] = None,
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

    def single_serialize(self, model: Any) -> Any:
        """Serialize nested Pydantic models into JSON-safe values."""
        if isinstance(model, BaseModel):
            return model.model_dump(
                mode="json",
                include=self.include,
                exclude=self.exclude,
                by_alias=self.by_alias,
                exclude_unset=self.exclude_unset,
                exclude_defaults=self.exclude_defaults,
                exclude_none=self.exclude_none,
                exclude_computed_fields=self.exclude_computed_fields,
                context=self.context,
                fallback=self.fallback,
            )
        if isinstance(model, Mapping):
            return {key: self.single_serialize(value) for key, value in model.items()}
        if self.is_sequence(model):
            return self.multiple_serialize(model)
        return model

    def multiple_serialize(self, model: Sequence[Any]) -> list[Any]:
        return [self.single_serialize(item) for item in model]


class PydanticDeserializer(BaseDeserializer[BaseModel]):
    """Deserialize values with :meth:`TypeAdapter.validate_python`."""

    def get_data(self, response: Response) -> Any:
        """Parse a response body as deserializer input."""
        return response.json()

    base_model_type: type[BaseModel] = BaseModel

    def __init__(
        self,
        model: Any,
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
        self._type_adapter = TypeAdapter(model)
        super().__init__(model=model)

    def single_deserialize(self, data: Any) -> Any:
        """Validate one value against the configured model annotation."""
        return self._type_adapter.validate_python(
            data,
            extra=self.extra,
            strict=self.strict,
            context=self.context,
            by_alias=self.by_alias,
            by_name=self.by_name,
        )

    def deserialize(self, data: Any) -> Any:
        """Validate data while preserving collection model annotations."""
        return self.single_deserialize(data)
