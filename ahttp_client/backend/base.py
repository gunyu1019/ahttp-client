from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional
    from ..request import RequestCore


class BaseBackend(ABC):
    @abstractmethod
    def get_request_kwargs(self, request_obj: RequestCore) -> dict[str, Any]:
        pass

    @property
    @abstractmethod
    def response_cls(self) -> type[Any]:
        pass

    @abstractmethod
    def response_data(self, response_obj: Any) -> bytes:
        pass

    @abstractmethod
    def response_text(self, response_obj: Any) -> str:
        pass

    @abstractmethod
    def response_json(
            self, response_obj: Any,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Optional[Any]:
        pass


class BaseBackendSession(ABC):
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