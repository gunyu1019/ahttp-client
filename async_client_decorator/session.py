import asyncio
from abc import ABC

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

    def close(self):
        return self.session.close()
