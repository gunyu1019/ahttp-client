from abc import ABC, abstractmethod


class BaseBackendSession:
    pass


class AsyncBackendSession(BaseBackendSession, ABC):
    @abstractmethod
    async def wrapped_close(self):
        pass

    @abstractmethod
    async def wrapped_request(self, method: str, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_get(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_post(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_options(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_delete(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_patch(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def wrapped_put(self, path: str, **kwargs):
        pass


class SyncBackendSession(BaseBackendSession, ABC):
    @abstractmethod
    def wrapped_close(self):
        pass

    @abstractmethod
    def wrapped_request(self, method: str, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_get(self, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_post(self, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_options(self, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_delete(self, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_patch(self, path: str, **kwargs):
        pass

    @abstractmethod
    def wrapped_put(self, path: str, **kwargs):
        pass