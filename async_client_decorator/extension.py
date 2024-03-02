from typing import Optional, TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    import asyncio

    from typing import Any, Callable
    from ._types import RequestAfterHookFunction, RequestBeforeHookFunction
    from .query import Query
    from .request import RequestCore, request
    from .session import Session


def multiple_hook(
    hook: Callable[
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
else:
    is_pydantic = True


def get_pydantic_response_model(
    model: "pydantic.BaseModel",
    index: Optional[int] = None,
    *,
    strict: Optional[bool] = None,
    from_attributes: Optional[bool] = None,
    context: Optional[dict[str, Any]] = None
):
    if not is_pydantic:
        raise ModuleNotFoundError("pydantic is not installed.")

    def decorator(func: RequestCore):
        @multiple_hook(func.after_hook, index=index)
        async def wrapper(_, response: dict[str, Any] | aiohttp.ClientResponse):
            if isinstance(response, aiohttp.ClientResponse):
                data = await response.json()
            else:
                data = response

            validated_data = model.model_validate(
                obj=data,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
            )
            return validated_data

    return decorator
