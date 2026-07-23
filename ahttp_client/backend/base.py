from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable, Optional, ClassVar
    from ..request import RequestCore

_BackendT = TypeVar("_BackendT", bound="BaseBackend")


class BaseBackend(ABC):
    """Base adapter for a supported HTTP client library.

    A backend creates the client session, converts :class:`RequestCore` values
    to client-specific keyword arguments, and exposes a common response
    interface. Subclasses that define both ``session_cls`` and ``response_cls``
    are registered automatically.
    """

    session_cls: ClassVar[type[Any]]
    response_cls: ClassVar[type[Any]]
    native_base_url: ClassVar[bool] = False

    _registry: ClassVar[dict[type[Any], type[BaseBackend]]] = {}

    def __init__(
        self,
        session: type[Any],
        *,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Create a backend and its underlying HTTP client session.

        Parameters
        ----------
        session: type
            HTTP client session class handled by this backend.
        base_url: Optional[str]
            Base URL forwarded to clients that support a native base URL.
        **kwargs
            Keyword arguments forwarded to the client session constructor.
        """
        if self.native_base_url and base_url is not None:
            kwargs["base_url"] = base_url
        self.session = session(**kwargs)
        self.session_kwargs = kwargs

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register a concrete backend for its configured session class."""
        super(BaseBackend, cls).__init_subclass__(**kwargs)

        if not hasattr(cls, "response_cls") or not hasattr(cls, "session_cls"):
            return

        BaseBackend._registry[cls.session_cls] = cls

    @classmethod
    def from_session(cls: type[_BackendT], session: type[Any], **kwargs: Any) -> _BackendT:
        """Create the backend registered for an HTTP client session class.

        Parameters
        ----------
        session: type
            Supported HTTP client session class.
        **kwargs
            Keyword arguments forwarded to the backend constructor.

        Raises
        ------
        TypeError
            If ``session`` is not registered with a backend.
        """
        if session not in cls._registry.keys():
            raise TypeError(f"{session.__name__} is not supported")
        backend_cls = cls._registry[session]
        if not issubclass(backend_cls, cls):
            raise TypeError(f"{session.__name__} is not supported by {cls.__name__}")
        return backend_cls(session, **kwargs)

    @abstractmethod
    def get_request_kwargs(self, request_obj: RequestCore[Any, Any]) -> dict[str, Any]:
        """Convert a request descriptor into client-specific request arguments."""
        pass

    @abstractmethod
    def response_data(self, response_obj: Any) -> bytes:
        """Return the response body as bytes."""
        pass

    @abstractmethod
    def response_text(self, response_obj: Any) -> str:
        """Return the response body decoded as text."""
        pass

    @abstractmethod
    def response_json(
        self,
        response_obj: Any,
        json_parser: Optional[Callable[..., Any]] = None,
        json_kwargs: Optional[dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Parse the response body as JSON using an optional custom parser."""
        pass

    @abstractmethod
    def response_status(self, response_obj: Any) -> int:
        """Return the HTTP status code from a client response."""
        pass

    @abstractmethod
    def response_headers(self, response_obj: Any) -> dict[str, Any]:
        """Return response headers as a dictionary."""
        pass

    @abstractmethod
    def response_url(self, response_obj: Any) -> str:
        """Return the URL associated with a client response."""
        pass

    @abstractmethod
    def response_close(self, response_obj: Any) -> None | Awaitable[None]:
        """Close a client response object."""
        pass

    @abstractmethod
    def response_closed(self, response_obj: Any) -> Optional[bool]:
        """Return response close state, or ``None`` if it is unavailable."""
        pass

    @property
    @abstractmethod
    def session_closed(self) -> bool:
        """Return whether the underlying HTTP client session is closed."""
        pass


class AsyncBackend(BaseBackend, ABC):
    """Base adapter contract for asynchronous HTTP client libraries."""

    async def pre_read_response(self, response_obj: Any) -> None:
        """Read a response before it is exposed through :class:`Response`.

        Backends that require eager reads can override this method.
        """
        pass

    @abstractmethod
    async def session_close(self) -> None:
        """Close the underlying asynchronous HTTP client session."""
        pass

    @abstractmethod
    async def session_request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous HTTP request with the given method and path."""
        pass

    @abstractmethod
    async def session_get(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``GET`` request."""
        pass

    @abstractmethod
    async def session_post(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``POST`` request."""
        pass

    @abstractmethod
    async def session_options(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``OPTIONS`` request."""
        pass

    @abstractmethod
    async def session_delete(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``DELETE`` request."""
        pass

    @abstractmethod
    async def session_patch(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``PATCH`` request."""
        pass

    @abstractmethod
    async def session_put(self, path: str, **kwargs: Any) -> Any:
        """Make an asynchronous ``PUT`` request."""
        pass


class SyncBackend(BaseBackend, ABC):
    """Base adapter contract for synchronous HTTP client libraries."""

    @abstractmethod
    def session_close(self) -> None:
        """Close the underlying synchronous HTTP client session."""
        pass

    @abstractmethod
    def session_request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make a synchronous HTTP request with the given method and path."""
        pass

    @abstractmethod
    def session_get(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``GET`` request."""
        pass

    @abstractmethod
    def session_post(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``POST`` request."""
        pass

    @abstractmethod
    def session_options(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``OPTIONS`` request."""
        pass

    @abstractmethod
    def session_delete(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``DELETE`` request."""
        pass

    @abstractmethod
    def session_patch(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``PATCH`` request."""
        pass

    @abstractmethod
    def session_put(self, path: str, **kwargs: Any) -> Any:
        """Make a synchronous ``PUT`` request."""
        pass
