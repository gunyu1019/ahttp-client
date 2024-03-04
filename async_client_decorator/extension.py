from __future__ import annotations

import inspect
from collections.abc import Iterable
from types import GenericAlias
from typing import overload, TYPE_CHECKING, TypeVar

import aiohttp

T = TypeVar("T")

if TYPE_CHECKING:
    import asyncio

    from abc import ABC, abstractmethod
    from typing import Any, Callable, Generic, Optional
    from ._types import RequestAfterHookFunction, RequestBeforeHookFunction
    from .query import Query
    from .request import RequestCore, request
    from .session import Session

    CallableT = TypeVar("CallableT")
    CallableR = TypeVar("CallableR")

    class BoundedMethod(ABC, Generic[T, CallableT, CallableR]):
        @abstractmethod
        @property
        def __self__(self) -> T: ...

        @abstractmethod
        @property
        def __func__(self) -> Callable[[T, CallableT], CallableR]: ...

    MultipleHookT = (
        BoundedMethod[T, CallableT, CallableR] | Callable[[CallableT], CallableR]
    )


def multiple_hook(
    hook: MultipleHookT[
        RequestCore,
        [RequestAfterHookFunction | RequestBeforeHookFunction],
        RequestAfterHookFunction | RequestBeforeHookFunction,
    ],
    index: Optional[int] = -1,
):
    """Use this method, if more than one pre-invoke hooks or post-invoke hooks need.

    Parameters
    ----------
    hook: Callable[
            [RequestAfterHookFunction | RequestBeforeHookFunction],
            RequestAfterHookFunction | RequestBeforeHookFunction
        ]
        Contains the decorator function used for hooking.
        This can be :meth:`RequestObj.before_hook` or :meth:`RequestObj.after_hook`.
    index: Optional[int]
        Order of invocation in invoke-hook

    Warnings
    --------
    This feature is experimental. It might not work as expected.

    Examples
    --------
    >>> class MetroAPI(Session):
    ...    def __init__(self, loop: asyncio.AbstractEventLoop):
    ...        super().__init__("https://api.yhs.kr", loop=loop)
    ...
    ...    @request("GET", "/metro/station")
    ...    async def station_search_with_query(
    ...            self,
    ...            response: aiohttp.ClientResponse,
    ...            name: Query | str
    ...    ) -> dict[str, Any]:
    ...        return await response.json()
    ...
    ...    @multiple_hook(station_search_with_query.before_hook)
    ...    async def before_hook_1(self, obj, path):
    ...        # Set-up before request
    ...        return obj, path
    ...
    ...    @multiple_hook(station_search_with_query.before_hook)
    ...    async def before_hook_2(self, obj, path):
    ...        # Set-up before request
    ...        return obj, path
    """
    hook_name = hook.__name__
    instance = hook.__self__

    is_exist_multiple_hook = True
    if not hasattr(instance, "__multiple_%s__" % hook_name):
        is_exist_multiple_hook = False
        setattr(instance, "__multiple_%s__" % hook_name, [])

    def decorator(func):
        getattr(instance, "__multiple_%s__" % hook_name).append((func, index))
        return func

    async def wrapper(wrapped_instance, *args):
        _args = tuple(args)
        multiple_hook_func = getattr(instance, "__multiple_%s__" % hook_name)
        sorted_multiple_hook_func = sorted(multiple_hook_func, key=lambda x: x[1])
        for func, _ in sorted_multiple_hook_func:
            _args = await func(wrapped_instance, *_args)
        return _args

    if not is_exist_multiple_hook:
        hook.__func__(instance, wrapper)
    return decorator


# Pydantic Model Validate
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
    model: BaseModelT,
    /,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
) -> list[BaseModelT]: ...


def _parsing_json_to_model(
    data: dict[Any, ...],
    model: BaseModelT,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None,
) -> BaseModelT:
    if isinstance(data, Iterable):
        validated_data = [
            model.model_validate(
                obj=x,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
            )
            for x in data
        ]
    else:
        validated_data = model.model_validate(
            obj=data,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
    return validated_data


def get_pydantic_response_model(
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
    ...    @get_pydantic_response_model(ResponseModel)
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
