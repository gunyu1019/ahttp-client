"""MIT License

Copyright (c) 2023-present gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import functools
import inspect
import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .backend.base import SyncBackend, AsyncBackend
from .request import RequestCore

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any, Optional, Self

    from ._types import RequestFunction
    from .request import RequestCore as _RequestCore

_log = logging.getLogger(__name__)


class BaseSession(ABC):
    """A class to manage session for managing decoration functions."""

    def __init__(
            self,
            base_url: str,
            *,
            directly_response: bool = False,
            _is_single_session: bool = False
    ):
        self.directly_response = directly_response
        self.base_url = base_url

        if not _is_single_session:
            for name, func in inspect.getmembers(self):
                if not isinstance(func, RequestCore):
                    continue

                func.session = self

    @staticmethod
    def _has_overridden_method(method):
        """Return False if the method is not overridden. Otherwise returns True if the overridden method."""
        return not hasattr(method, "__special_method__")

    @staticmethod
    def _special_method(func):
        func.__special_method__ = None
        return func

    @property
    @abstractmethod
    def closed(self) -> bool:
        pass


class AsyncSession(BaseSession):
    def __init__(
            self,
            base_url: str,
            session: type,
            *,
            directly_response: bool = False,
            _is_single_session: bool = False,
            **kwargs,
    ):
        super(AsyncSession, self).__init__(
            base_url,
            directly_response=directly_response,
            _is_single_session=_is_single_session,
        )
        self.session = session(**kwargs)
        self.backend: AsyncBackend = AsyncBackend.from_session(session, **kwargs)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
            self,
            exc_type: Optional[type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ):
        await self.close()

    async def close(self):
        await self.backend.session_close()

    async def request(self, method: str, path: str, **kwargs):
        return await self.backend.session_request(method, path, **kwargs)

    async def get(self, path: str, **kwargs):
        return await self.backend.session_get(path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.backend.session_post(path, **kwargs)

    async def options(self, path: str, **kwargs):
        return await self.backend.session_options(path, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self.backend.session_delete(path, **kwargs)

    async def patch(self, path: str, **kwargs):
        return await self.backend.session_patch(path, **kwargs)

    async def put(self, path: str, **kwargs):
        return await self.backend.session_put(path, **kwargs)

    async def _make_request(self, request: RequestCore, path: str):
        _req_obj = request
        _path = path

        if self._has_overridden_method(self.before_request):
            _req_obj, _path = await self.before_request(request, path)

        request_kwargs = self.backend.get_request_kwargs(_req_obj)
        _log.debug("Request Called: [%s] %s" % (_req_obj.method, _path))
        response = await self.backend.session_request(_req_obj.method, _path, **request_kwargs)
        await self.backend.pre_read_response(response)

        if self._has_overridden_method(self.after_request):
            response = await self.after_request(response)
        return response

    @BaseSession._special_method
    async def before_request(self, request: RequestCore, path: str) -> tuple[RequestCore, str]:
        """A special method that acts as a session local pre-invoke hook.
        This is similar to :meth:`RequestCore.before_request`.

        When :meth:`RequestCore.before_request` exists, this method is called after
        :meth:`RequestCore.before_request` called.

        Parameters
        ----------
        request: RequestCore
            The instance of RequestCore.
        path: str
            The final string of the request url.

        Returns
        -------
        Tuple[RequestCore, str]
            The return type must be the same as the parameter.
        """
        return request, path

    @BaseSession._special_method
    async def after_request(self, response: Any) -> Any:
        """A special method that acts as a session local post-invoke.
        This is similar to :meth:`RequestCore.after_request`.

        When :meth:`RequestCore.after_request` exists, this method is called before
        :meth:`RequestCore.after_request` called.

        Parameters
        ----------
        response: Any
            The result of HTTP request.

        Returns
        -------
        Any | T
            Cleanup response HTTP results.
            If RequestCore.after_request exists, the response type of :meth:`RequestCore.after_request` will follow
            the type of this method.
        """
        return response

    @classmethod
    def single_session(cls, base_url: str, **session_kwargs):
        """A single session for one request.

        Parameters
        ----------
        base_url: str
            base url of the API. (for example, https://api.yhs.kr)

        Examples
        --------
        The session is defined through the function's decoration.

        >>> @AsyncSession.single_session("https://api.yhs.kr")
        ... @request("GET", "/bus/station")
        ... async def station_query(session: AsyncSession, name: typing.Annotated[str, Query]) -> Any:
        ...     pass

        """

        def decorator(func: "_RequestCore") -> RequestFunction:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                client = cls(base_url, _is_single_session=True, **session_kwargs)
                func.session = client
                response = await func(*args, **kwargs)
                if not client.closed:
                    await client.close()
                return response

            wrapper.__core__ = func  # type: ignore[attr-defined]
            wrapper.before_hook = func.before_hook  # type: ignore[attr-defined]
            wrapper.after_hook = func.after_hook  # type: ignore[attr-defined]
            return wrapper

        return decorator


class Session(BaseSession):
    def __init__(
            self,
            base_url: str,
            session: type,
            *,
            directly_response: bool = False,
            _is_single_session: bool = False,
            **kwargs,
    ):
        super(Session, self).__init__(
            base_url,
            directly_response=directly_response,
            _is_single_session=_is_single_session,
        )
        self.session = session(**kwargs)
        self.backend: SyncBackend = SyncBackend.from_session(session, **kwargs)

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self,
            exc_type: Optional[type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ):
        self.close()

    def close(self):
        self.backend.session_close()

    def request(self, method: str, path: str, **kwargs):
        return self.backend.session_request(method, path, **kwargs)

    def get(self, path: str, **kwargs):
        return self.backend.session_get(path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.backend.session_post(path, **kwargs)

    def options(self, path: str, **kwargs):
        return self.backend.session_options(path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.backend.session_delete(path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.backend.session_patch(path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.backend.session_put(path, **kwargs)

    def _make_request(self, request: RequestCore, path: str):
        _req_obj = request
        _path = path

        if self._has_overridden_method(self.before_request):
            _req_obj, _path = self.before_request(request, path)

        request_kwargs = self.backend.get_request_kwargs(_req_obj)
        _log.debug("Request Called: [%s] %s" % (_req_obj.method, _path))
        response = self.backend.session_request(_req_obj.method, _path, **request_kwargs)

        if self._has_overridden_method(self.after_request):
            response = self.after_request(response)
        return response

    @BaseSession._special_method
    def before_request(self, request: RequestCore, path: str) -> tuple[RequestCore, str]:
        """A special method that acts as a session local pre-invoke hook.
        This is similar to :meth:`RequestCore.before_request`.

        When :meth:`RequestCore.before_request` exists, this method is called after
        :meth:`RequestCore.before_request` called.

        Parameters
        ----------
        request: RequestCore
            The instance of RequestCore.
        path: str
            The final string of the request url.

        Returns
        -------
        Tuple[RequestCore, str]
            The return type must be the same as the parameter.
        """
        return request, path

    @BaseSession._special_method
    def after_request(self, response: Any) -> Any:
        """A special method that acts as a session local post-invoke.
        This is similar to :meth:`RequestCore.after_request`.

        When :meth:`RequestCore.after_request` exists, this method is called before
        :meth:`RequestCore.after_request` called.

        Parameters
        ----------
        response: Any
            The result of HTTP request.

        Returns
        -------
        Any | T
            Cleanup response HTTP results.
            If RequestCore.after_request exists, the response type of :meth:`RequestCore.after_request` will follow
            the type of this method.
        """
        return response

    @classmethod
    def single_session(cls, base_url: str, **session_kwargs):
        """A single session for one request.

        Parameters
        ----------
        base_url: str
            base url of the API. (for example, https://api.yhs.kr)

        Examples
        --------
        The session is defined through the function's decoration.

        >>> @Session.single_session("https://api.yhs.kr")
        ... @request("GET", "/bus/station")
        ... async def station_query(session: SyncSession, name: typing.Annotated[str, Query]) -> Any:
        ...     pass

        """

        def decorator(func: "_RequestCore") -> RequestFunction:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                client = cls(base_url, _is_single_session=True, **session_kwargs)
                func.session = client
                response = func(*args, **kwargs)
                if not client.closed:
                    client.close()
                return response

            wrapper.__core__ = func  # type: ignore[attr-defined]
            wrapper.before_hook = func.before_hook  # type: ignore[attr-defined]
            wrapper.after_hook = func.after_hook  # type: ignore[attr-defined]
            return wrapper

        return decorator
