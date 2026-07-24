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

import asyncio
import math
import time
from typing import Awaitable, Any, Callable, Optional, cast

from ._types import RequestDecorator
from .exception import HTTPServerError
from .request import RequestCore
from .response import Response


class RetryConfig:
    """Configure retry attempts, exception matching, and exponential backoff.

    Parameters
    ----------
    max_retries: int
        Maximum number of attempts after the initial request.
    backoff_factor: float
        Multiplier used to calculate the exponential delay before each retry.
    retry_on: tuple[type[Exception], ...]
        Exception classes that trigger another attempt.
    max_delay: Optional[float]
        Maximum delay in seconds, or ``None`` for no upper bound.
    retry_unsafe: bool
        Whether retries are explicitly allowed for non-idempotent HTTP
        methods such as POST and PATCH.

    Raises
    ------
    TypeError
        If a retry count, delay, or exception filter has an invalid type.
    ValueError
        If a retry count or delay is negative or non-finite.

    Notes
    -----
    ``max_retries`` excludes the initial request. The delay before retry
    attempt ``n`` is ``backoff_factor * 2 ** (n - 1)`` and is capped by
    ``max_delay`` when an upper bound is configured.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        retry_on: tuple[type[Exception], ...] = (HTTPServerError,),
        max_delay: Optional[float] = None,
        retry_unsafe: bool = False,
    ) -> None:
        if isinstance(max_retries, bool) or not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to zero")

        if isinstance(backoff_factor, bool) or not isinstance(backoff_factor, (int, float)):
            raise TypeError("backoff_factor must be a number")
        if backoff_factor < 0 or not math.isfinite(backoff_factor):
            raise ValueError("backoff_factor must be a finite non-negative number")

        if max_delay is not None:
            if isinstance(max_delay, bool) or not isinstance(max_delay, (int, float)):
                raise TypeError("max_delay must be a number or None")
            if max_delay < 0 or not math.isfinite(max_delay):
                raise ValueError("max_delay must be a finite non-negative number")

        if not isinstance(retry_on, tuple) or not all(
            isinstance(exception_type, type) and issubclass(exception_type, Exception) for exception_type in retry_on
        ):
            raise TypeError("retry_on must contain only Exception subclasses")
        if not isinstance(retry_unsafe, bool):
            raise TypeError("retry_unsafe must be a boolean")

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on
        self.max_delay = max_delay
        self.retry_unsafe = retry_unsafe

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RetryConfig):
            return False
        return (
            self.max_retries == other.max_retries
            and self.backoff_factor == other.backoff_factor
            and self.retry_on == other.retry_on
            and self.max_delay == other.max_delay
            and self.retry_unsafe == other.retry_unsafe
        )

    def _backoff_delay(self, attempt: int) -> float:
        """Return the delay in seconds for a one-based retry attempt."""
        if self.backoff_factor == 0:
            return 0.0
        if self.max_delay is not None:
            if self.backoff_factor >= self.max_delay:
                return float(self.max_delay)
            maximum_exponent = math.log2(self.max_delay / self.backoff_factor)
            if attempt - 1 >= maximum_exponent:
                return float(self.max_delay)

        delay = self.backoff_factor * (2 ** (attempt - 1))
        if self.max_delay is not None:
            delay = min(delay, self.max_delay)
        return float(delay)

    async def execute_async(
        self, make_request_func: Callable[..., Awaitable[tuple[Response, Any]]]
    ) -> tuple[Response, Any]:
        """Execute an asynchronous request and retry matching failures.

        Parameters
        ----------
        make_request_func: Callable[..., Awaitable[tuple[Response, Any]]]
            Zero-argument callable that returns the raw response and the
            response-pipeline result.

        Returns
        -------
        tuple[Response, Any]
            Raw response and processed result from the successful attempt.

        Raises
        ------
        Exception
            Re-raises a non-matching exception immediately or the last
            matching exception after the retry budget is exhausted.
        """
        attempt = 0
        while True:
            if attempt > 0:
                await asyncio.sleep(self._backoff_delay(attempt))
            try:
                return await make_request_func()
            except Exception as exc:
                if not isinstance(exc, self.retry_on) or attempt >= self.max_retries:
                    raise
                attempt += 1

    def execute_sync(self, make_request_func: Callable[..., tuple[Response, Any]]) -> tuple[Response, Any]:
        """Execute a synchronous request and retry matching failures.

        Parameters
        ----------
        make_request_func: Callable[..., tuple[Response, Any]]
            Zero-argument callable that returns the raw response and the
            response-pipeline result.

        Returns
        -------
        tuple[Response, Any]
            Raw response and processed result from the successful attempt.

        Raises
        ------
        Exception
            Re-raises a non-matching exception immediately or the last
            matching exception after the retry budget is exhausted.
        """
        attempt = 0
        while True:
            if attempt > 0:
                time.sleep(self._backoff_delay(attempt))
            try:
                return make_request_func()
            except Exception as exc:
                if not isinstance(exc, self.retry_on) or attempt >= self.max_retries:
                    raise
                attempt += 1


def retry(
    max_retries: int = 3,
    *,
    backoff_factor: float = 1.0,
    retry_on: tuple[type[Exception], ...] | type[Exception] = (HTTPServerError,),
    max_delay: Optional[float] = None,
    retry_unsafe: bool = False,
) -> RequestDecorator[Any, Any]:
    """Decorate a request to retry on failure with exponential backoff.

    Parameters
    ----------
    max_retries: int
        Maximum number of retry attempts after the initial request.
    backoff_factor: float
        Multiplier applied to the exponential backoff delay.
        ``delay = backoff_factor * 2 ** (attempt - 1)``
    retry_on: tuple[type[Exception], ...] | type[Exception]
        Exception types that trigger a retry attempt. Defaults to
        :class:`HTTPServerError` (5xx responses).
    max_delay: Optional[float]
        Upper bound on the sleep delay in seconds. ``None`` means no cap.
    retry_unsafe: bool
        Explicitly allow retries for non-idempotent methods. Defaults to
        ``False`` so POST, PATCH, and other unsafe requests are not repeated
        accidentally.

    Returns
    -------
    RequestDecorator[Any, Any]
        Decorator that attaches the retry configuration to a request.

    Raises
    ------
    TypeError
        If a retry count, delay, or exception filter has an invalid type.
    ValueError
        If a retry count or delay is negative or non-finite.

    Notes
    -----
    Exceptions raised by request transport or a session-level
    ``after_request`` hook are eligible for retry. Request-level ``after_hook``
    callbacks run after the retry operation and are outside its scope.
    """
    if isinstance(retry_on, type):
        retry_on = (retry_on,)
    config = RetryConfig(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        retry_on=retry_on,
        max_delay=max_delay,
        retry_unsafe=retry_unsafe,
    )

    def decorator(func: RequestDecorator[Any, Any] | RequestCore[Any, Any]) -> Any:
        if isinstance(func, RequestCore):
            func._bind_retry(config)
            return func
        extension_target: Any = func
        if not hasattr(extension_target, "__extension__"):
            extension_target.__extension__ = dict()
        extension_target.__extension__["retry"] = config
        return func

    return cast(RequestDecorator[Any, Any], decorator)
