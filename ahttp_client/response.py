from __future__ import annotations

from asyncio import iscoroutinefunction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional
    from .backend.base import BaseBackend


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
    def __init__(self, response_obj: Any, backend: BaseBackend):
        self._raw_response_obj = response_obj
        self._backend = backend

        self._closed = False

    @property
    def raw(self) -> Any:
        """Return the original response object from the HTTP client library."""
        return self._raw_response_obj

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
            raise TypeError("close() cannot be called on a synchronous backend")
        self._backend.response_close(self._raw_response_obj)
        self._closed = True

    async def async_close(self) -> None:
        """Close the underlying HTTP response."""
        if not iscoroutinefunction(self._backend.response_close):
            raise TypeError("async_close() can only be called on an asynchronous backend")
        await self._backend.response_close(self._raw_response_obj)
        self._closed = True

    def text(self) -> str:
        """Return the response body decoded as text."""
        return self._backend.response_text(self._raw_response_obj)

    def json(
            self,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Any:
        """Parse the response body as JSON.

        Parameters
        ----------
        json_parser: Optional[Callable[[Any, ...], Any]]
            Custom JSON parser. The backend default parser is used when empty.
        json_kwargs: Optional[dict[str, Any]]
            Keyword arguments passed to ``json_parser`` or the backend parser.
        """
        return self._backend.response_json(self._raw_response_obj, json_parser, json_kwargs)

    def content(self) -> bytes:
        """Return the response body as bytes."""
        return self._backend.response_data(self._raw_response_obj)
