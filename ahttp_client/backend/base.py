from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional
    from ..request import RequestCore


class BaseBackend(ABC):
    def __init__(self, session: type, **kwargs: Any):
        self.session = session(**kwargs)
        self.session_kwargs = kwargs

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

    @abstractmethod
    def response_status(self, response_obj: Any) -> int:
        pass

    @abstractmethod
    def response_headers(self, response_obj: Any) -> dict[str, Any]:
        pass

    @abstractmethod
    def response_url(self, response_obj: Any) -> str:
        pass


class AsyncBackend(BaseBackend, ABC):
    @abstractmethod
    async def session_close(self):
        pass

    @abstractmethod
    async def session_request(self, method: str, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_get(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_post(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_options(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_delete(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_patch(self, path: str, **kwargs):
        pass

    @abstractmethod
    async def session_put(self, path: str, **kwargs):
        pass


class SyncBackend(BaseBackend, ABC):
    @abstractmethod
    def session_close(self):
        pass

    @abstractmethod
    def session_request(self, method: str, path: str, **kwargs):
        pass

    @abstractmethod
    def session_get(self, path: str, **kwargs):
        pass

    @abstractmethod
    def session_post(self, path: str, **kwargs):
        pass

    @abstractmethod
    def session_options(self, path: str, **kwargs):
        pass

    @abstractmethod
    def session_delete(self, path: str, **kwargs):
        pass

    @abstractmethod
    def session_patch(self, path: str, **kwargs):
        pass

    @abstractmethod
    def session_put(self, path: str, **kwargs):
        pass