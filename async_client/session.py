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

import asyncio
import functools

import aiohttp

from ._types import RequestFunction


class Session:
    """A class to manage session for managing decoration functions."""

    def __init__(self, base_url: str, directly_response: bool = False, **kwargs):
        self.directly_response = directly_response
        self.base_url = base_url

        self.session = aiohttp.ClientSession(self.base_url, **kwargs)

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

    @classmethod
    def single_session(
        cls, base_url: str, loop: asyncio.AbstractEventLoop = None, **session_kwargs
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
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("function %s must be coroutine.".format(func.__name__))

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                client = cls(base_url, loop, **session_kwargs)
                response = await func(client, *args, **kwargs)
                if not client.closed:
                    await client.close()
                return response

            return wrapper

        return decorator
