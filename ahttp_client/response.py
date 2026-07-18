from __future__ import annotations

from asyncio import iscoroutinefunction
from typing import TYPE_CHECKING, Any, Awaitable, Callable, cast, TypeVar

if TYPE_CHECKING:
    from typing import Optional
    from .backend.base import BaseBackend
    from .serialization.base import BaseDeserializer

ModelT = TypeVar("ModelT")


class Response:
    """A common response wrapper for supported HTTP client libraries.

    The wrapper exposes response information through a consistent interface and
    keeps the original response object available through :attr:`raw`.

    Parameters
    ----------
    response_obj: Any
        Original response object returned by the HTTP client library.
    backend: BaseBackend
        Backend that provides response operations for ``response_obj``.
    """

    def __init__(self, response_obj: Any, backend: BaseBackend, serializer: Optional[BaseDeserializer] = None):
        self._raw_response_obj = response_obj
        self._backend = backend
        self._deserializer = serializer

        self._closed = False

    @property
    def raw(self) -> Any:
        """Return the original response object from the HTTP client library."""
        return self._raw_response_obj

    @property
    def model(self) -> Optional[ModelT]:
        if self._deserializer is None:
            return None
        data = self._deserializer.get_data(self)
        return self._deserializer.deserialize(data)

    @property
    def session(self) -> Any:
        """Return the original HTTP client session that created this response."""
        return self._backend.session

    @property
    def header(self) -> dict[str, Any]:
        """Return response headers as a dictionary."""
        return self._backend.response_headers(self._raw_response_obj)

    @property
    def status(self) -> int:
        """Return the HTTP response status code."""
        return self._backend.response_status(self._raw_response_obj)

    @property
    def url(self) -> str:
        """Return the URL of the HTTP response."""
        return self._backend.response_url(self._raw_response_obj)

    @property
    def closed(self) -> bool:
        """Return whether the response has been closed."""
        return self._backend.response_closed(self._raw_response_obj) or self._closed

    def close(self) -> None:
        """Close the underlying HTTP response."""
        if iscoroutinefunction(self._backend.response_close):
            raise TypeError("close() cannot be called on an asynchronous response backend")
        close = cast(Callable[[Any], None], self._backend.response_close)
        close(self._raw_response_obj)
        self._closed = True

    async def async_close(self) -> None:
        """Close the underlying HTTP response."""
        if not iscoroutinefunction(self._backend.response_close):
            raise TypeError("async_close() requires an asynchronous response-close backend")
        close = cast(Callable[[Any], Awaitable[None]], self._backend.response_close)
        await close(self._raw_response_obj)
        self._closed = True

    def text(self) -> str:
        """Return the response body decoded as text."""
        return self._backend.response_text(self._raw_response_obj)

    def json(
        self,
        json_parser: Optional[Callable[..., Any]] = None,
        json_kwargs: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Parse the response body as JSON.

        Parameters
        ----------
        json_parser: Optional[Callable[..., Any]]
            Custom JSON parser. The backend default parser is used when empty.
        json_kwargs: Optional[dict[str, Any]]
            Keyword arguments passed to ``json_parser`` or the backend parser.
        """
        return self._backend.response_json(self._raw_response_obj, json_parser, json_kwargs)

    def content(self) -> bytes:
        """Return the response body as bytes."""
        return self._backend.response_data(self._raw_response_obj)

    def raise_for_status(self) -> None:
        """Raise the exception matching this response's 4xx or 5xx status.

        Unknown statuses in either error range raise :class:`HTTPClientError`
        or :class:`HTTPServerError` respectively.  Other status codes return
        without raising an exception.
        """
        from .exception import exception_for_status

        exception = exception_for_status(self.status)
        if exception is not None:
            raise exception(self)
