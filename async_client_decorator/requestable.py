import asyncio
from abc import ABC

import aiohttp


class Requestable(ABC):
    def __init__(
            self,
            base_url: str,
            loop: asyncio.AbstractEventLoop = None,
            **kwargs
    ):
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
