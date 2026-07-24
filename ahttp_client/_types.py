"""MIT License

Copyright (c) 2021 gunyu1019

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
from typing import (
    Any,
    Awaitable,
    BinaryIO,
    Callable,
    Coroutine,
    IO,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)
from io import IOBase

T = TypeVar("T")
P = ParamSpec("P")
RequestCoreT = TypeVar("RequestCoreT")
AsyncRequestCoreT_co = TypeVar("AsyncRequestCoreT_co", covariant=True)
SyncRequestCoreT_co = TypeVar("SyncRequestCoreT_co", covariant=True)

# Request descriptors support both synchronous and asynchronous functions.
# Concrete core classes validate the appropriate callable kind at runtime.
RequestFunction = Callable[P, T]
AsyncRequestFunction = Callable[P, Coroutine[Any, Any, T]]
AsyncRequestBeforeHookFunction = Callable[[Any, RequestCoreT, str], Awaitable[tuple[RequestCoreT, str]]]
SyncRequestBeforeHookFunction = Callable[[Any, RequestCoreT, str], tuple[RequestCoreT, str]]
AsyncRequestAfterHookFunction = Callable[[Any, Any], Awaitable[T]]
SyncRequestAfterHookFunction = Callable[[Any, Any], T]

RequestBeforeHookFunction = AsyncRequestBeforeHookFunction[Any] | SyncRequestBeforeHookFunction[Any]
RequestAfterHookFunction = AsyncRequestAfterHookFunction[Any] | SyncRequestAfterHookFunction[Any]


class RequestDecorator(Protocol[AsyncRequestCoreT_co, SyncRequestCoreT_co]):
    """Map coroutine functions to async cores and regular functions to sync cores."""

    @overload
    def __call__(self, func: AsyncRequestFunction[..., T]) -> AsyncRequestCoreT_co: ...

    @overload
    def __call__(self, func: RequestFunction[..., T]) -> SyncRequestCoreT_co: ...


ValidationFunction = Callable[[Any, T], T]


class ValidationDecorator(Protocol):
    """Preserve a validator's value type when it is registered."""

    def __call__(self, func: ValidationFunction[T]) -> ValidationFunction[T]: ...


_IO_TYPE = (IO, BinaryIO, IOBase)
_BODY_JSON_TYPE = (dict, list, tuple)
