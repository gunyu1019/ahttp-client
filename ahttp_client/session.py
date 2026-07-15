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

from .backend.base import BaseBackend, SyncBackend, AsyncBackend
from .request_bound import RequestBound, RequestAsyncBound, RequestSyncBound
from .response import Response

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any, Optional, Self

    from .request import RequestCore
    from ._types import RequestFunction

_log = logging.getLogger(__name__)


class BaseSession(ABC):
    """Base class for sessions that own and execute request descriptors.

    Subclasses select a supported HTTP client through a backend adapter. When
    a decorated request is accessed on a session instance, it is bound to that
    session and can be called as a regular synchronous or asynchronous method.
    """
    backend: BaseBackend

    def __init__(
            self,
            base_url: str,
            *,
            directly_response: bool = False,
            _is_single_session: bool = False
    ):
        self.directly_response = directly_response
        self.base_url = base_url

        self._request_bound_func: dict[RequestCore, RequestBound] = dict()

    @staticmethod
    def _has_overridden_method(method):
        """Return whether a session hook was overridden by a subclass."""
        return not hasattr(method, "__special_method__")

    @staticmethod
    def _special_method(func):
        func.__special_method__ = None
        return func

    @property
    @abstractmethod
    def closed(self) -> bool:
        pass

    def _get_request_url(self, path: str) -> str:
        if self.backend.native_base_url:
            return path
        if not path.startswith("/") and not self.base_url.endswith("/"):
            return self.base_url + "/" + path
        return self.base_url + path

    @abstractmethod
    def _make_request(self, request: RequestCore, path: str) -> Response:
        pass

    @abstractmethod
    def _get_request_bound(self, request: RequestCore) -> RequestBound:
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
        self.backend: AsyncBackend = AsyncBackend.from_session(session, base_url=base_url, **kwargs)
        super(AsyncSession, self).__init__(
            base_url,
            directly_response=directly_response,
            _is_single_session=_is_single_session,
        )

        self._request_bound_func: dict[RequestCore, RequestAsyncBound] = dict()

    @property
    def closed(self) -> bool:
        return self.backend.session_closed

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
        url = self._get_request_url(path)
        return await self.backend.session_request(method, url, **kwargs)

    async def get(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_get(url, **kwargs)

    async def post(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_post(url, **kwargs)

    async def options(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_options(url, **kwargs)

    async def delete(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_delete(url, **kwargs)

    async def patch(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_patch(url, **kwargs)

    async def put(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return await self.backend.session_put(url, **kwargs)

    async def _make_request(self, request: RequestCore, path: str):
        _req_obj = request

        if self._has_overridden_method(self.before_request):
            _req_obj, path = await self.before_request(request, path)

        request_kwargs = self.backend.get_request_kwargs(_req_obj)
        _log.debug("Request Called: [%s] %s" % (_req_obj.method, path))
        url = self._get_request_url(path)
        raw_response = await self.backend.session_request(_req_obj.method.__str__(), url, **request_kwargs)
        await self.backend.pre_read_response(raw_response)
        response = Response(raw_response, self.backend)

        if self._has_overridden_method(self.after_request):
            response = await self.after_request(response)
        return response

    @BaseSession._special_method
    async def before_request(self, request: RequestCore, path: str) -> tuple[RequestCore, str]:
        """Run after a request-level pre-hook and before dispatching the request.

        Override this method to alter the request object or final path for all
        requests made by this session.

        Parameters
        ----------
        request: RequestCore
            Request descriptor prepared for this invocation.
        path: str
            Request path after path parameters have been substituted.

        Returns
        -------
        tuple[RequestCore, str]
            Request descriptor and path to dispatch.
        """
        return request, path

    @BaseSession._special_method
    async def after_request(self, response: Any) -> Any:
        """Run after the backend receives a response and before a request hook.

        Override this method to transform the :class:`Response` for every
        request made by this session.

        Parameters
        ----------
        response: Any
            Response returned by the backend.

        Returns
        -------
        Any
            Value passed to the request-level post-hook or decorated function.
        """
        return response

    @classmethod
    def single_session(cls, base_url: str, session: type, **session_kwargs):
        """Decorate a request to create and close a session per invocation.

        The wrapper creates ``session`` with ``base_url`` and ``session_kwargs``
        for the call, then closes it after the request completes.

        Parameters
        ----------
        base_url: str
            Base URL of the API.
        session: type
            The HTTP session class to use (e.g. aiohttp.ClientSession, httpx.AsyncClient).

        """

        def decorator(func: RequestCore) -> RequestFunction:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                client = cls(base_url, session, _is_single_session=True, **session_kwargs)
                try:
                    response = await func._execute(client, *args, **kwargs)
                finally:
                    if not client.closed:
                        await client.close()
                return response

            wrapper.__core__ = func  # type: ignore[attr-defined]
            wrapper.before_hook = func.before_hook  # type: ignore[attr-defined]
            wrapper.after_hook = func.after_hook  # type: ignore[attr-defined]
            return wrapper

        return decorator

    def _get_request_bound(self, request_obj: RequestCore) -> RequestAsyncBound:
        if request_obj.name not in self._request_bound_func.keys():
            self._request_bound_func[request_obj.name] = RequestAsyncBound(request_obj, self)
        return self._request_bound_func[request_obj.name]


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
        self.backend: SyncBackend = SyncBackend.from_session(session, base_url=base_url, **kwargs)
        super(Session, self).__init__(
            base_url,
            directly_response=directly_response,
            _is_single_session=_is_single_session,
        )
        self._request_bound_func: dict[RequestCore, RequestSyncBound] = dict()

    @property
    def closed(self) -> bool:
        return self.backend.session_closed

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
        url = self._get_request_url(path)
        return self.backend.session_request(method, url, **kwargs)

    def get(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_get(url, **kwargs)

    def post(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_post(url, **kwargs)

    def options(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_options(url, **kwargs)

    def delete(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_delete(url, **kwargs)

    def patch(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_patch(url, **kwargs)

    def put(self, path: str, **kwargs):
        url = self._get_request_url(path)
        return self.backend.session_put(url, **kwargs)

    def _make_request(self, request: RequestCore, path: str):
        _req_obj = request

        if self._has_overridden_method(self.before_request):
            _req_obj, path = self.before_request(request, path)

        request_kwargs = self.backend.get_request_kwargs(_req_obj)
        url = self._get_request_url(path)
        _log.debug("Request Called: [%s] %s" % (_req_obj.method, path))
        raw_response = self.backend.session_request(_req_obj.method.__str__(), url, **request_kwargs)
        response = Response(raw_response, self.backend)

        if self._has_overridden_method(self.after_request):
            response = self.after_request(response)
        return response

    @BaseSession._special_method
    def before_request(self, request: RequestCore, path: str) -> tuple[RequestCore, str]:
        """Run after a request-level pre-hook and before dispatching the request.

        Override this method to alter the request object or final path for all
        requests made by this session.

        Parameters
        ----------
        request: RequestCore
            Request descriptor prepared for this invocation.
        path: str
            Request path after path parameters have been substituted.

        Returns
        -------
        tuple[RequestCore, str]
            Request descriptor and path to dispatch.
        """
        return request, path

    @BaseSession._special_method
    def after_request(self, response: Any) -> Any:
        """Run after the backend receives a response and before a request hook.

        Override this method to transform the :class:`Response` for every
        request made by this session.

        Parameters
        ----------
        response: Any
            Response returned by the backend.

        Returns
        -------
        Any
            Value passed to the request-level post-hook or decorated function.
        """
        return response

    @classmethod
    def single_session(cls, base_url: str, session: type, **session_kwargs):
        """Decorate a request to create and close a session per invocation.

        The wrapper creates ``session`` with ``base_url`` and ``session_kwargs``
        for the call, then closes it after the request completes.

        Parameters
        ----------
        base_url: str
            Base URL of the API.
        session: type
            The HTTP session class to use (e.g. requests.Session, httpx.Client).

        """

        def decorator(func: RequestCore) -> RequestFunction:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                client = cls(base_url, session, _is_single_session=True, **session_kwargs)
                response = func._execute(client, *args, **kwargs)
                if not client.closed:
                    client.close()
                return response

            wrapper.__core__ = func  # type: ignore[attr-defined]
            wrapper.before_hook = func.before_hook  # type: ignore[attr-defined]
            wrapper.after_hook = func.after_hook  # type: ignore[attr-defined]
            return wrapper

        return decorator

    def _get_request_bound(self, request_obj: RequestCore) -> RequestSyncBound:
        if request_obj not in self._request_bound_func.keys():
            self._request_bound_func[request_obj] = RequestSyncBound(request_obj, self)
        return self._request_bound_func[request_obj]
