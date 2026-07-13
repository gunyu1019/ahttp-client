import aiohttp

from .base import AsyncBackendSession


class AiohttpSession(aiohttp.ClientSession, AsyncBackendSession):
    async def wrapped_close(self):
        await self.close()

    async def wrapped_request(self, method: str, path: str, **kwargs):
        return await self.request(method, path, **kwargs)

    async def wrapped_get(self, path: str, **kwargs):
        return await self.get(path, **kwargs)

    async def wrapped_post(self, path: str, **kwargs):
        return await self.post(path, **kwargs)

    async def wrapped_options(self, path: str, **kwargs):
        return await self.options(path, **kwargs)

    async def wrapped_delete(self, path: str, **kwargs):
        return await self.delete(path, **kwargs)

    async def wrapped_patch(self, path: str, **kwargs):
        return await self.patch(path, **kwargs)

    async def wrapped_put(self, path: str, **kwargs):
        return await self.put(path, **kwargs)
