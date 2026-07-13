import httpx

from .base import AsyncBackendSession, SyncBackendSession


class HttpXAsyncSession(httpx.AsyncClient, AsyncBackendSession):
    async def wrapped_close(self):
        await self.aclose()

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


class HttpXSyncSession(httpx.Client, SyncBackendSession):
    def wrapped_close(self):
        self.close()

    def wrapped_request(self, method: str, path: str, **kwargs):
        return self.request(method, path, **kwargs)

    def wrapped_get(self, path: str, **kwargs):
        return self.get(path, **kwargs)

    def wrapped_post(self, path: str, **kwargs):
        return self.post(path, **kwargs)

    def wrapped_options(self, path: str, **kwargs):
        return self.options(path, **kwargs)

    def wrapped_delete(self, path: str, **kwargs):
        return self.delete(path, **kwargs)

    def wrapped_patch(self, path: str, **kwargs):
        return self.patch(path, **kwargs)

    def wrapped_put(self, path: str, **kwargs):
        return self.put(path, **kwargs)
