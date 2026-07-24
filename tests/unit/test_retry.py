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
import io
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ahttp_client import AsyncSession, BaseSession, Body, Response, request
from ahttp_client.enum import DirectResponseType
from ahttp_client.exception import HTTPServerError, HTTPClientError
from ahttp_client.retry import RetryConfig, retry


class _RawResponse:
    def __init__(self) -> None:
        self.closed = False


class _SyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    def response_close(self, response: _RawResponse) -> None:
        response.closed = True


class _AsyncBackend:
    session = object()

    def response_closed(self, response: _RawResponse) -> bool:
        return response.closed

    async def response_close(self, response: _RawResponse) -> None:
        response.closed = True


class _FailingPreReadBackend(_AsyncBackend):
    native_base_url = False
    session = object()

    def __init__(self, response: _RawResponse) -> None:
        self.response = response

    def get_request_kwargs(self, request_core) -> dict[str, Any]:
        return {}

    async def session_request(
            self, method: str, url: str, **kwargs: Any
    ) -> _RawResponse:
        return self.response

    async def pre_read_response(self, response: _RawResponse) -> None:
        raise OSError("body pre-read failed")


class _FailingClosePreReadBackend(_FailingPreReadBackend):
    def response_close(self, response: _RawResponse) -> None:
        raise RuntimeError("cleanup failed")


def _make_sync_response() -> Response:
    return Response(_RawResponse(), _SyncBackend())


def _make_async_response() -> Response:
    return Response(_RawResponse(), _AsyncBackend())


def test_async_make_request_closes_response_when_pre_read_fails() -> None:
    raw_response = _RawResponse()
    session = object.__new__(AsyncSession)
    session.backend = _FailingPreReadBackend(raw_response)
    session.base_url = "https://example.test"

    @request("GET", "/")
    async def endpoint(session) -> None: ...

    with pytest.raises(OSError, match="body pre-read failed"):
        asyncio.run(session._make_request(endpoint, "/"))

    assert raw_response.closed is True


def test_async_make_request_preserves_pre_read_error_when_cleanup_fails() -> None:
    raw_response = _RawResponse()
    session = object.__new__(AsyncSession)
    session.backend = _FailingClosePreReadBackend(raw_response)
    session.base_url = "https://example.test"

    @request("GET", "/")
    async def endpoint(session) -> None: ...

    with pytest.raises(OSError, match="body pre-read failed"):
        asyncio.run(session._make_request(endpoint, "/"))


class _SyncSession:
    directly_response = DirectResponseType.RESPONSE

    def __init__(self, responses: list[Response | Exception]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    def _make_request(self, request_core, path: str) -> tuple[Response, Any]:
        item = self._responses[self._call_count]
        self._call_count += 1
        if isinstance(item, Exception):
            raise item
        return item, item

    def _has_overridden_method(self, method) -> bool:
        return type(self).after_request is not _SyncSession.after_request

    def after_request(self, response: Response) -> Any:
        return response


class _AsyncSession:
    directly_response = DirectResponseType.RESPONSE

    def __init__(self, responses: list[Response | Exception]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    async def _make_request(self, request_core, path: str) -> tuple[Response, Any]:
        item = self._responses[self._call_count]
        self._call_count += 1
        if isinstance(item, Exception):
            raise item
        return item, item

    def _has_overridden_method(self, method) -> bool:
        return type(self).after_request is not _AsyncSession.after_request

    async def after_request(self, response: Response) -> Any:
        return response


def test_retry_rewinds_seekable_body_stream() -> None:
    class RetriableError(Exception):
        pass

    class ReplaySession:
        directly_response = False

        def __init__(self) -> None:
            self.reads: list[bytes] = []

        def _make_request(self, request_core, path: str) -> tuple[Response, Any]:
            self.reads.append(request_core.body.read())
            if len(self.reads) == 1:
                raise RetriableError("retry")
            response = _make_sync_response()
            return response, response

    @retry(max_retries=1, backoff_factor=0, retry_on=RetriableError, retry_unsafe=True)
    @request("POST", "/")
    def upload(
        session: BaseSession,
        stream: Annotated[io.BytesIO, Body],
    ) -> str:
        return "ok"

    session = ReplaySession()
    assert upload._execute(session, io.BytesIO(b"payload")) == "ok"
    assert session.reads == [b"payload", b"payload"]


def test_retry_rejects_non_seekable_body_stream() -> None:
    class NonSeekable:
        def read(self) -> bytes:
            return b"payload"

    @retry(max_retries=1, backoff_factor=0, retry_unsafe=True)
    @request("POST", "/")
    def upload(
        session: BaseSession,
        stream: Annotated[io.IOBase, Body],
    ) -> None:
        pass

    with pytest.raises(TypeError, match="must be seekable"):
        upload._execute(_SyncSession([]), NonSeekable())


# ---------------------------------------------------------------------------
# Decorator binding
# ---------------------------------------------------------------------------

def test_retry_applied_after_request_binds_config_directly() -> None:
    """@retry applied after @request calls _bind_retry immediately."""

    @retry(max_retries=5, backoff_factor=2.0)
    @request("GET", "/")
    async def endpoint(session) -> None: ...

    assert endpoint._retry_config is not None
    assert endpoint._retry_config.max_retries == 5
    assert endpoint._retry_config.backoff_factor == 2.0


def test_retry_applied_before_request_binds_via_extension() -> None:
    """@retry applied before @request stashes config through __extension__."""

    @request("GET", "/")
    @retry(max_retries=2)
    async def endpoint(session) -> None: ...

    assert endpoint._retry_config is not None
    assert endpoint._retry_config.max_retries == 2


@pytest.mark.parametrize("decorator_order", ["retry_first", "request_first"])
def test_retry_rejects_non_idempotent_method_without_opt_in(decorator_order: str) -> None:
    async def endpoint(session) -> None:
        pass

    with pytest.raises(ValueError, match="retry_unsafe=True"):
        if decorator_order == "retry_first":
            retry(max_retries=1)(request("POST", "/")(endpoint))
        else:
            request("PATCH", "/")(retry(max_retries=1)(endpoint))


def test_retry_allows_non_idempotent_method_with_explicit_opt_in() -> None:
    @retry(max_retries=1, retry_unsafe=True)
    @request("POST", "/")
    async def endpoint(session) -> None:
        pass

    assert endpoint._retry_config is not None
    assert endpoint._retry_config.retry_unsafe is True


def test_zero_retries_does_not_require_unsafe_opt_in() -> None:
    @retry(max_retries=0)
    @request("POST", "/")
    async def endpoint(session) -> None:
        pass

    assert endpoint._retry_config is not None


def test_retry_default_retry_on_is_http_server_error() -> None:
    config = RetryConfig()
    assert config.retry_on == (HTTPServerError,)


def test_retry_single_exception_type_is_normalized_to_tuple() -> None:
    @retry(retry_on=HTTPClientError)
    @request("GET", "/")
    async def endpoint(session) -> None: ...

    assert endpoint._retry_config.retry_on == (HTTPClientError,)


@pytest.mark.parametrize(
    ("kwargs", "exception_type", "message"),
    [
        ({"max_retries": -1}, ValueError, "max_retries"),
        ({"max_retries": 1.5}, TypeError, "max_retries"),
        ({"max_retries": True}, TypeError, "max_retries"),
        ({"backoff_factor": -0.1}, ValueError, "backoff_factor"),
        ({"backoff_factor": float("inf")}, ValueError, "backoff_factor"),
        ({"backoff_factor": float("nan")}, ValueError, "backoff_factor"),
        ({"backoff_factor": "slow"}, TypeError, "backoff_factor"),
        ({"max_delay": -0.1}, ValueError, "max_delay"),
        ({"max_delay": float("inf")}, ValueError, "max_delay"),
        ({"max_delay": float("nan")}, ValueError, "max_delay"),
        ({"max_delay": "never"}, TypeError, "max_delay"),
        ({"retry_on": ValueError}, TypeError, "retry_on"),
        ({"retry_on": (ValueError(),)}, TypeError, "retry_on"),
        ({"retry_on": (BaseException,)}, TypeError, "retry_on"),
        ({"retry_unsafe": 1}, TypeError, "retry_unsafe"),
    ],
)
def test_retry_config_rejects_invalid_values(
        kwargs: dict[str, Any],
        exception_type: type[Exception],
        message: str,
) -> None:
    with pytest.raises(exception_type, match=message):
        RetryConfig(**kwargs)


def test_retry_decorator_rejects_invalid_retry_on_immediately() -> None:
    with pytest.raises(TypeError, match="retry_on"):
        retry(retry_on=ValueError())


# ---------------------------------------------------------------------------
# Successful request — no retry needed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_no_retry_on_success(is_async: bool) -> None:
    good_response = _make_async_response() if is_async else _make_sync_response()

    if is_async:
        @retry(max_retries=3)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([good_response])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = asyncio.run(endpoint._execute(session))
        mock_sleep.assert_not_called()
    else:
        @retry(max_retries=3)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([good_response])
        with patch("time.sleep") as mock_sleep:
            result = endpoint._execute(session)
        mock_sleep.assert_not_called()

    assert result is good_response
    assert session._call_count == 1


# ---------------------------------------------------------------------------
# Retry on matching exception
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_retries_on_matching_exception_and_succeeds(is_async: bool) -> None:
    err = HTTPServerError()
    good_response = _make_async_response() if is_async else _make_sync_response()

    if is_async:
        @retry(max_retries=2, backoff_factor=1.0)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err, good_response])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = asyncio.run(endpoint._execute(session))
        mock_sleep.assert_called_once_with(1.0)
    else:
        @retry(max_retries=2, backoff_factor=1.0)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err, good_response])
        with patch("time.sleep") as mock_sleep:
            result = endpoint._execute(session)
        mock_sleep.assert_called_once_with(1.0)

    assert result is good_response
    assert session._call_count == 2


# ---------------------------------------------------------------------------
# Exhausted retries — last exception is re-raised
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_raises_after_max_retries_exhausted(is_async: bool) -> None:
    err = HTTPServerError()

    if is_async:
        @retry(max_retries=2, backoff_factor=1.0)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err, err, err])
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(HTTPServerError):
                asyncio.run(endpoint._execute(session))
    else:
        @retry(max_retries=2, backoff_factor=1.0)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err, err, err])
        with patch("time.sleep"):
            with pytest.raises(HTTPServerError):
                endpoint._execute(session)

    assert session._call_count == 3


# ---------------------------------------------------------------------------
# Non-matching exception propagates immediately
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_non_matching_exception_is_not_retried(is_async: bool) -> None:
    err = HTTPClientError()

    if is_async:
        @retry(max_retries=3, retry_on=(HTTPServerError,))
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(HTTPClientError):
                asyncio.run(endpoint._execute(session))
        mock_sleep.assert_not_called()
    else:
        @retry(max_retries=3, retry_on=(HTTPServerError,))
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err])
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(HTTPClientError):
                endpoint._execute(session)
        mock_sleep.assert_not_called()

    assert session._call_count == 1


# ---------------------------------------------------------------------------
# Backoff delay values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_backoff_delays_follow_exponential_formula(is_async: bool) -> None:
    err = HTTPServerError()
    good_response = _make_async_response() if is_async else _make_sync_response()

    if is_async:
        @retry(max_retries=3, backoff_factor=2.0)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err, err, err, good_response])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            asyncio.run(endpoint._execute(session))
        calls = [c.args[0] for c in mock_sleep.call_args_list]
    else:
        @retry(max_retries=3, backoff_factor=2.0)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err, err, err, good_response])
        with patch("time.sleep") as mock_sleep:
            endpoint._execute(session)
        calls = [c.args[0] for c in mock_sleep.call_args_list]

    # attempt 1: 2.0 * 2^0 = 2.0
    # attempt 2: 2.0 * 2^1 = 4.0
    # attempt 3: 2.0 * 2^2 = 8.0
    assert calls == [2.0, 4.0, 8.0]


# ---------------------------------------------------------------------------
# max_delay cap
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_max_delay_caps_sleep_duration(is_async: bool) -> None:
    err = HTTPServerError()
    good_response = _make_async_response() if is_async else _make_sync_response()

    if is_async:
        @retry(max_retries=3, backoff_factor=10.0, max_delay=5.0)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err, err, err, good_response])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            asyncio.run(endpoint._execute(session))
        calls = [c.args[0] for c in mock_sleep.call_args_list]
    else:
        @retry(max_retries=3, backoff_factor=10.0, max_delay=5.0)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err, err, err, good_response])
        with patch("time.sleep") as mock_sleep:
            endpoint._execute(session)
        calls = [c.args[0] for c in mock_sleep.call_args_list]

    assert all(d <= 5.0 for d in calls)


def test_max_delay_caps_backoff_before_float_overflow() -> None:
    config = RetryConfig(
        max_retries=2000,
        backoff_factor=1.0,
        max_delay=10.0,
    )

    assert config._backoff_delay(1025) == 10.0


# ---------------------------------------------------------------------------
# Failed response is closed before retry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_transport_error_retried_without_response_to_close(is_async: bool) -> None:
    """When _make_request raises (transport error), retry fires with no
    response to close since the request never completed."""
    err = HTTPServerError()
    good_response = _make_async_response() if is_async else _make_sync_response()

    if is_async:
        @retry(max_retries=2)
        @request("GET", "/")
        async def endpoint(session) -> None: ...

        session = _AsyncSession([err, good_response])
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = asyncio.run(endpoint._execute(session))
        mock_sleep.assert_called_once()
    else:
        @retry(max_retries=2)
        @request("GET", "/")
        def endpoint(session) -> None: ...

        session = _SyncSession([err, good_response])
        with patch("time.sleep") as mock_sleep:
            result = endpoint._execute(session)
        mock_sleep.assert_called_once()

    assert session._call_count == 2
    assert result is good_response
