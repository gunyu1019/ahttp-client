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

import aiohttp
from typing import TYPE_CHECKING, TypeVar

T = TypeVar("T")

if TYPE_CHECKING:
    from abc import ABC, abstractmethod
    from typing import Callable, Generic, Optional
    from .._types import RequestAfterHookFunction, RequestBeforeHookFunction
    from ..query import Query
    from ..request import RequestCore, request
    from ..response import Response
    from ..session import AsyncSession

    CallableT = TypeVar("CallableT")
    CallableR = TypeVar("CallableR")

    class BoundedMethod(ABC, Generic[T, CallableT, CallableR]):
        @abstractmethod
        @property
        def __self__(self) -> T: ...

        @abstractmethod
        @property
        def __func__(self) -> Callable[[T, CallableT], CallableR]: ...

    MultipleHookT = BoundedMethod[T, CallableT, CallableR] | Callable[[CallableT], CallableR]


def multiple_hook(
    hook: MultipleHookT[
        RequestCore,
        (RequestAfterHookFunction | RequestBeforeHookFunction),
        RequestAfterHookFunction | RequestBeforeHookFunction,
    ],
    index: Optional[int] = -1,
):
    """Register an additional request pre-hook or post-hook.

    Hooks run in ascending ``index`` order. Each hook receives the previous
    hook's return value as its arguments and must return the arguments for the
    next hook.

    Parameters
    ----------
    hook: Callable[
            (RequestAfterHookFunction | RequestBeforeHookFunction),
            RequestAfterHookFunction | RequestBeforeHookFunction
        ]
        Bound ``before_hook`` or ``after_hook`` decorator of a request core.
    index: Optional[int]
        Invocation order; hooks with lower values run first.

    Warnings
    --------
    Additional hooks are currently asynchronous and are intended for async
    request cores.
    """
    hook_name = hook.__name__  # type: ignore[union-attr]
    instance = hook.__self__  # type: ignore[union-attr]

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
        hook.__func__(instance, wrapper)  # type: ignore[union-attr]
    return decorator
