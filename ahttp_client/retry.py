from __future__ import annotations

import asyncio
import math
import time
from typing import Awaitable, Any, Callable, Optional

from ._types import RequestDecorator
from .exception import HTTPServerError
from .request import RequestCore
from .response import Response


class RetryConfig:
    def __init__(
            self,
            max_retries: int = 3,
            backoff_factor: float = 1.0,
            retry_on: tuple[type[Exception], ...] = (HTTPServerError,),
            max_delay: Optional[float] = None,
    ) -> None:
        if isinstance(max_retries, bool) or not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to zero")

        if (
                isinstance(backoff_factor, bool)
                or not isinstance(backoff_factor, (int, float))
        ):
            raise TypeError("backoff_factor must be a number")
        if backoff_factor < 0 or not math.isfinite(backoff_factor):
            raise ValueError("backoff_factor must be a finite non-negative number")

        if max_delay is not None:
            if (
                    isinstance(max_delay, bool)
                    or not isinstance(max_delay, (int, float))
            ):
                raise TypeError("max_delay must be a number or None")
            if max_delay < 0 or not math.isfinite(max_delay):
                raise ValueError("max_delay must be a finite non-negative number")

        if not isinstance(retry_on, tuple) or not all(
                isinstance(exception_type, type)
                and issubclass(exception_type, Exception)
                for exception_type in retry_on
        ):
            raise TypeError("retry_on must contain only Exception subclasses")

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on
        self.max_delay = max_delay

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RetryConfig):
            return False
        return (
            self.max_retries == other.max_retries
            and self.backoff_factor == other.backoff_factor
            and self.retry_on == other.retry_on
            and self.max_delay == other.max_delay
        )

    def _backoff_delay(self, attempt: int) -> float:
        delay = self.backoff_factor * (2 ** (attempt - 1))
        if self.max_delay is not None:
            delay = min(delay, self.max_delay)
        return delay

    async def execute_async(
            self,
            make_request_func: Callable[..., Awaitable[tuple[Response, Any]]]
    ) -> tuple[Response, Any]:
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

    def execute_sync(
            self,
            make_request_func: Callable[..., tuple[Response, Any]]
    ) -> tuple[Response, Any]:
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
    """
    if isinstance(retry_on, type):
        retry_on = (retry_on,)
    config = RetryConfig(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        retry_on=retry_on,
        max_delay=max_delay,
    )

    def decorator(func: RequestDecorator[Any, Any] | RequestCore):
        if isinstance(func, RequestCore):
            func._bind_retry(config)
            return func
        extension_target: Any = func
        if not hasattr(extension_target, "__extension__"):
            extension_target.__extension__ = dict()
        extension_target.__extension__["retry"] = config
        return func

    return decorator
