import asyncio
from abc import ABC
from typing import NoReturn

import aiohttp


class Session(ABC):
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
