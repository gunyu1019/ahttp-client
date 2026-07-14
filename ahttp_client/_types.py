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
from typing import Any, TypeVar, Callable, Coroutine, IO, BinaryIO, TYPE_CHECKING
from io import IOBase

if TYPE_CHECKING:
    from .session import BaseSession
    from .request import RequestCore


T = TypeVar("T")

RequestFunction = Callable[..., Coroutine[Any, Any, Any]]
RequestBeforeHookFunction = Callable[
    [BaseSession, RequestCore, str],
    Coroutine[Any, Any, tuple[RequestCore, str]],
]
RequestAfterHookFunction = Callable[
    [BaseSession, Any],
    Coroutine[Any, Any, Any],
]

_IO_TYPE = (IO, BinaryIO, IOBase)
_BODY_JSON_TYPE = (dict, list, tuple)