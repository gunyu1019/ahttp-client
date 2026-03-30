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

from __future__ import annotations

import inspect
import aiohttp

from collections.abc import Sequence
from types import GenericAlias
from typing import overload, TypeVar, TYPE_CHECKING

from .multiple_hook import multiple_hook
from ..component import EmptyComponent
from ..utils import *

if TYPE_CHECKING:
    from typing import Any, Optional, Literal, Callable

    from ..component import Component
    from ..request import RequestCore

try:
    import pydantic
except (ModuleNotFoundError, ImportError):
    is_pydantic = False
    BaseModelT = TypeVar("BaseModelT")
else:
    is_pydantic = True
    BaseModelT = TypeVar("BaseModelT", bound=type[pydantic.BaseModel])


@overload
def _parsing_json_to_model(
    data: list[Any],
    model: type[BaseModelT],
    /,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
) -> Optional[list[BaseModelT]]: ...


@overload
def _parsing_json_to_model(
    data: dict[Any, ...],
    model: type[BaseModelT],
    /,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
) -> Optional[BaseModelT]: ...


def _parsing_json_to_model(
    data: dict[Any, ...] | list[Any],
    model: type[BaseModelT],
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
) -> Optional[BaseModelT | list[BaseModelT]]:
    if isinstance(data, Sequence):
        validated_data = [
            model.model_validate(
                obj=x,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
            )
            for x in data
        ]
    elif isinstance(data, type(None)):
        return None
    else:
        validated_data = model.model_validate(
            obj=data,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
    return validated_data


@overload
def _parsing_model_to_json(
    data: Optional[list[BaseModelT]],
    /,
    *,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    context: Optional[dict[str, Any]] = None,
    fallback: Optional[Callable[[Any], Any]] = None,
) -> Optional[list[dict[str, Any]]]:
    ...


@overload
def _parsing_model_to_json(
        data: Optional[BaseModelT],
        /,
        *,
        by_alias: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_computed_fields: bool = False,
        context: Optional[dict[str, Any]] = None,
        fallback: Optional[Callable[[Any], Any]] = None,
) -> Optional[dict[str, Any]]:
    ...


def _parsing_model_to_json(
    data: Optional[BaseModelT | list[BaseModelT]],
    /,
    *,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    context: Optional[dict[str, Any]] = None,
    fallback: Optional[Callable[[Any], Any]] = None,
) -> Optional[dict[str, Any] | list[dict[str, Any]]]:
    if isinstance(data, (list, tuple)):
        dumped_data = [
            _parsing_model_to_json(
                x,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                exclude_computed_fields=exclude_computed_fields,
                context=context,
                fallback=fallback,
            )
            for x in data
        ]
    elif isinstance(data, type(None)):
        return None
    else:
        dumped_data = data.model_dump(
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            context=context,
            fallback=fallback,
        )
    return dumped_data


def is_pydantic_model(data: Any) -> bool:
    if isinstance(data, (list, tuple)):
        return is_pydantic_model(data[0])
    return isinstance(data, pydantic.BaseModel)


def pydantic_request_model(
    index: Optional[int] = None,
    *,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    context: Optional[Any] = None,
    fallback: Optional[Callable[[Any], Any]] = None,
):
    """A decorator that the `request` objects to provide parsing from raw data into a pydantic model.

    Parameters
    ----------
    index : Optional[int]
        Order of invocation in invoke-hook.
        The order is recommended to be last after the status check.
    by_alias : bool | None
        Same feature as parameter of pydantic.BaseModel.model_dump method named by_alias.
    exclude_unset : bool
        Same feature as parameter of pydantic.BaseModel.model_dump method named exclude_unset.
    exclude_defaults : bool
        Same feature as parameter of pydantic.BaseModel.model_dump method named exclude_defaults.
    exclude_none : bool
        Same feature as parameter of pydantic.BaseModel.model_dump method named exclude_none.
    exclude_computed_fields : bool
        Same feature as parameter of pydantic.BaseModel.model_dump method named exclude_computed_fields.
    context : Optional[Any]
        Same feature as parameter of pydantic.BaseModel.model_dump method named context.
    fallback : Optional[Callable[[Any], Any]]
        Same feature as parameter of pydantic.BaseModel.model_dump method named fallback.
    """
    if not is_pydantic:
        raise ModuleNotFoundError("pydantic is not installed.")

    def decorator(func: RequestCore) -> RequestCore:
        # If the Pydantic model is serialized, the body parameter type must be json, and all others must be data.
        # Therefore, as the argument state is abstract, it was defined as None.
        if func.body_parameter is not None:
            func.body_parameter_type = None

        @multiple_hook(func.before_hook, index=index)
        async def wrapper(_, request: RequestCore, path: str):
            for name, value in request.headers.items():
                if not is_pydantic_model(value):
                    continue

                request.headers[name] = _parsing_model_to_json(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    exclude_computed_fields=exclude_computed_fields,
                    context=context,
                    fallback=fallback
                ).__str__()  # noqa

            for name, value in request.params.items():
                if not is_pydantic_model(value):
                    continue
                request.params[name] = _parsing_model_to_json(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    exclude_computed_fields=exclude_computed_fields,
                    context=context,
                    fallback=fallback
                ).__str__()

            if is_pydantic_model(request.body):
                request.body_parameter_type = "json"
                request.body = _parsing_model_to_json(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    exclude_computed_fields=exclude_computed_fields,
                    context=context,
                    fallback=fallback
                )
            return request, path

        return func

    return decorator


def pydantic_response_model(
    model: Optional[BaseModelT] = None,
    /,
    index: Optional[int] = None,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
):
    """Create a request method to return a model extended by pydantic.BaseModel

    Parameters
    ----------
    model: Optional[pydantic.BaseModel]
        A model extended by pydantic.BaseModel to parse JSON.
        If directly_response enabled and model parameter is empty, model will followed return annotation.
        However, model parameter is empty, TypeError("Invalid model type.") will be raised.
    index: Optional[int]
        Order of invocation in invoke-hook.
        The order is recommended to be last after the status check.
    strict: Optional[bool]
        Same feature as parameter of pydantic.BaseModel.model_validate method named strict.
    from_attributes: Optional[bool]
        Same feature as parameter of pydantic.BaseModel.model_validate method named from_attributes.
    context: Optional[dict[str, Any]]
        Same feature as parameter of pydantic.BaseModel.model_validate method named context.

    Warnings
    --------
    This feature is experimental. It might not work as expected.
    And `pydatnic` pacakge required.

    Examples
    --------
    >>> class ResponseModel(pydantic.BaseModel):
    ...     name: str
    ...     id: str
    ...
    >>> class MetroAPI(Session):
    ...    def __init__(self, loop: asyncio.AbstractEventLoop):
    ...        super().__init__("https://api.yhs.kr", loop=loop)
    ...
    ...    @pydantic_response_model(ResponseModel)
    ...    @request("GET", "/metro/station")
    ...    async def station_search_with_query(
    ...            self,
    ...            response: aiohttp.ClientResponse,
    ...            name: Query | str
    ...    ) -> ResponseModel:
    ...        pass
    """
    if not is_pydantic:
        raise ModuleNotFoundError("pydantic is not installed.")

    def decorator(func: RequestCore) -> BaseModelT:
        _model = model
        if model is None and func.directly_response:
            _model = func._signature.return_annotation

        if _model is inspect.Signature.empty or _model is None:
            raise TypeError("Invalid model type.")

        if isinstance(_model, GenericAlias):
            _model = _model.__args__[0]

        @multiple_hook(func.after_hook, index=index)
        async def wrapper(_, response: dict[str, Any] | aiohttp.ClientResponse):
            if isinstance(response, aiohttp.ClientResponse):
                data = await response.json()
            else:
                data = response

            result = _parsing_json_to_model(
                data,
                _model,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
            )
            return result

        return func

    return decorator


# get_pydantic_response_model name had been changed to pydantic_model
get_pydantic_response_model = pydantic_response_model
