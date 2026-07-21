from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ahttp_client import Response, request
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


def _make_sync_response() -> Response:
    return Response(_RawResponse(), _SyncBackend())


def _make_async_response() -> Response:
    return Response(_RawResponse(), _AsyncBackend())


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
