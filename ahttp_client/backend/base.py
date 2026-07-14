from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, ClassVar
    from ..request import RequestCore

_BackendT = TypeVar('_BackendT', bound='BaseBackend')


class BaseBackend(ABC):
    session_cls: ClassVar[type]
    response_cls: ClassVar[type]
    native_base_url: ClassVar[bool] = False

    _registry: ClassVar[dict[type, type[BaseBackend]]] = {}

    def __init__(self, session: type, *, base_url: Optional[str] = None, **kwargs: Any):
        if self.native_base_url and base_url is not None:
            kwargs["base_url"] = base_url
        self.session = session(**kwargs)
        self.session_kwargs = kwargs

    def __init_subclass__(cls, **kwargs: Any):
        super(BaseBackend, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, 'response_cls') or not hasattr(cls, 'session_cls'):
            return

        BaseBackend._registry[cls.session_cls] = cls

    @classmethod
    def from_session(cls: type[_BackendT], session: type, **kwargs: Any) -> _BackendT:
        if session not in cls._registry.keys():
            raise TypeError(f'{session.__name__} is not supported')
        return cls._registry[session](session, **kwargs)  # type: ignore[return-value]

    @abstractmethod
    def get_request_kwargs(self, request_obj: RequestCore) -> dict[str, Any]:
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

    @abstractmethod
    def response_close(self, response_obj: Any) -> None:
        pass

    @property
    @abstractmethod
    def session_closed(self) -> bool:
        pass


class AsyncBackend(BaseBackend, ABC):
    async def pre_read_response(self, response_obj: Any) -> None:
        pass

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