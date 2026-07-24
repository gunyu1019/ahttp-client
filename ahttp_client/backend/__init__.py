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

from .base import BaseBackend, AsyncBackend, SyncBackend

__all__ = ["BaseBackend", "AsyncBackend", "SyncBackend"]

try:
    from .aiohttp import AiohttpBackend
except ModuleNotFoundError as exc:
    if exc.name != "aiohttp":
        raise
else:
    AiohttpSession = AiohttpBackend  # backward-compatible alias
    __all__ += ["AiohttpBackend", "AiohttpSession"]

try:
    from .httpx import HttpXAsyncSession, HttpXSyncSession
except ModuleNotFoundError as exc:
    if exc.name != "httpx":
        raise
else:
    __all__ += ["HttpXAsyncSession", "HttpXSyncSession"]

try:
    from .requests import RequestsBackend
except ModuleNotFoundError as exc:
    if exc.name != "requests":
        raise
else:
    RequestSession = RequestsBackend  # backward-compatible alias
    __all__ += ["RequestsBackend", "RequestSession"]
