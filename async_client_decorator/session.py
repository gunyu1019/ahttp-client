"""MIT License

Copyright (c) 2023 gunyu1019

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

import asyncio
import functools
import inspect
from typing import TYPE_CHECKING, Optional, Any

import aiohttp

from .request import RequestCore

if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType

    from ._types import RequestFunction


class Session:
    """A class to manage session for managing decoration functions."""
    def __init__(
            self,
            base_url: str,
            *,
            directly_response: bool = False,
            loop: asyncio.AbstractEventLoop = None,
            _is_single_session: bool = False,
            **kwargs
    ):
        self.directly_response = directly_response
        self.base_url = base_url
        self.loop = loop

        self.session = aiohttp.ClientSession(self.base_url, loop=self.loop, **kwargs)

        if not _is_single_session:
            for name, func in inspect.getmembers(self):
                if not isinstance(func, RequestCore):
                    continue

                func.session = self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        await self.close()

    @property
    def closed(self) -> bool:
        return self.session.closed

    async def close(self):
        return await self.session.close()

    async def request(self, method: str, path: str, **kwargs):
        return await self.session.request(method, path, **kwargs)

    async def get(self, path: str, **kwargs):
        return await self.session.get(path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.session.post(path, **kwargs)

    async def options(self, path: str, **kwargs):
        return await self.session.options(path, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self.session.delete(path, **kwargs)

    async def _make_request(self, request: RequestCore, path: str, **kwargs):
        _req_obj, _path = await self.before_request(request, path)
        request_kwargs = _req_obj.get_request_kwargs()
        return await self.session.request(_req_obj.method, _path, **request_kwargs)

    async def before_request(self, request: RequestCore, path: str) -> RequestCore:
        return request, path

    async def after_request(self, response: aiohttp.ClientResponse) -> Any:
        return response

    @classmethod
    def single_session(
            cls,
            base_url: str,
            loop: asyncio.AbstractEventLoop = None,
            **session_kwargs
    ):
        """A single session for one request.

        Parameters
        ----------
        base_url: str
            base url of the API. (for example, https://api.yhs.kr)
        loop: asyncio.AbstractEventLoop
            [event loop](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio-event-loop)
             used for processing HTTP requests.

        Examples
        --------
        The session is defined through the function's decoration.

        >>> @Session.single_session("https://api.yhs.kr")
        ... @request("GET", "/bus/station")
        ... async def station_query(session: Session, name: Query | str) -> aiohttp.ClientResponse:
        ...     pass

        """

        def decorator(func: RequestFunction):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                client = cls(base_url, loop=loop, _is_single_session=True, **session_kwargs)
                func.session = client
                response = await func(*args, **kwargs)
                if not client.closed:
                    await client.close()
                return response

            wrapper.__core__ = func
            wrapper.before_hook = func.before_hook
            wrapper.after_hook = func.after_hook
            return wrapper

        return decorator
