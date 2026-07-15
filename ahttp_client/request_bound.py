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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from .session import BaseSession, AsyncSession, Session
    from .request import RequestCore, AsyncRequestCore, SyncRequestCore


class RequestBound(ABC):
    """A request descriptor bound to a session instance.

    Request-bound objects are created automatically when a decorated request is
    accessed through a :class:`BaseSession`. They retain both the request core
    and the session used to execute it.
    """

    def __init__(self, core: RequestCore, session: BaseSession):
        self._core = core
        self._session = session

    @property
    def __core__(self) -> RequestCore:
        """Return the unbound request descriptor."""
        return self._core

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Any:
        """Execute the request with arguments for the decorated function."""
        pass


class RequestAsyncBound(RequestBound):
    """A request descriptor bound to an :class:`AsyncSession`."""

    _session: AsyncSession
    _core: AsyncRequestCore

    async def __call__(self, *args, **kwargs) -> Any:
        """Execute the asynchronous request."""
        return await self._core._execute(self._session, *args, **kwargs)


class RequestSyncBound(RequestBound):
    """A request descriptor bound to a :class:`Session`."""

    _session: Session
    _core: SyncRequestCore

    def __call__(self, *args, **kwargs) -> Any:
        """Execute the synchronous request."""
        return self._core._execute(self._session, *args, **kwargs)
