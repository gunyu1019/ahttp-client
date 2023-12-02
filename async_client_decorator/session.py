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
import aiohttp
from typing import NoReturn


class Session:
    def __init__(
            self,
            base_url: str,
            loop: asyncio.AbstractEventLoop = None,
            directly_response: bool = False,
            **kwargs
    ):
        self.directly_response = directly_response
        self.base_url = base_url

        if loop is None:
            loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=loop, **kwargs)

    def _get_url(self, path) -> str:
        return self.base_url + path

    async def request(self, method: str, path: str, **kwargs):
        url = self._get_url(path)
        return await self.session.request(method, url, **kwargs)

    async def close(self):
        return await self.session.close()

    def __enter__(self) -> NoReturn:
        raise TypeError("Use async with instead")

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb
    ) -> None:
        pass

    async def __aenter__(self) -> "Session":
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb
    ) -> None:
        await self.close()

    @classmethod
    def single_session(
            cls,
            base_url: str,
            loop: asyncio.AbstractEventLoop = None,
            **session_kwargs
    ):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("function %s must be coroutine.".format(func.__name__))

            async def wrapper(*args, **kwargs):
                client = cls(base_url, loop, **session_kwargs)
                response = await func(client, *args, **kwargs)
                if isinstance(response, aiohttp.ClientResponse):
                    await response.read()
                await client.close()
                return response
            return wrapper

        return decorator
