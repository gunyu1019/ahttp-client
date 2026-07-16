"""Lifecycle, hook, validation, and request-state integration coverage."""

from __future__ import annotations

import asyncio
import inspect
from typing import Annotated, Any

import pytest

from ahttp_client import AsyncSession, Header, Path, Query, Response, Session, get
from tests.integration.backend_matrix import (
    ASYNC_BACKEND_IDS,
    ASYNC_BACKENDS,
    BACKEND_BY_SESSION,
    SYNC_BACKEND_IDS,
    SYNC_BACKENDS,
)


class AsyncLifecycleAPI(AsyncSession):
    def __init__(self, base_url: str, backend: type, **kwargs: Any) -> None:
        super().__init__(base_url, backend, **kwargs)
        self.function_called = False
        self.after_called = False

    async def before_request(self, request: Any, path: str) -> tuple[Any, str]:
        request.headers["X-Session-Hook"] = "async"
        return request, path

    async def after_request(self, response: Response) -> Response:
        self.after_called = True
        return response

    @get("/echo/{resource}")
    async def validated(
        self,
        resource: Annotated[str, Path],
        value: Annotated[str, Query],
        response: Response,
        limit: Annotated[int, Query] = 10,
    ) -> dict[str, Any]:
        return response.json()

    @get("/echo")
    async def direct(self, response: Response) -> dict[str, Any]:
        self.function_called = True
        return response.json()

    @get("/echo")
    async def hooked(self, response: Response) -> dict[str, Any]:
        return response


@AsyncLifecycleAPI.validated.validation("value")
def _async_normalize_value(session: AsyncLifecycleAPI, value: str) -> str:
    return value.strip().upper()


@AsyncLifecycleAPI.hooked.before_hook
async def _async_request_before_hook(
    session: AsyncLifecycleAPI, request: Any, path: str
) -> tuple[Any, str]:
    request.headers["X-Request-Hook"] = "async"
    return request, path


@AsyncLifecycleAPI.hooked.after_hook
async def _async_request_after_hook(
    session: AsyncLifecycleAPI, response: Response
) -> dict[str, Any]:
    payload = response.json()
    payload["request_after"] = "async"
    return payload


class SyncLifecycleAPI(Session):
    def __init__(self, base_url: str, backend: type, **kwargs: Any) -> None:
        super().__init__(base_url, backend, **kwargs)
        self.function_called = False
        self.after_called = False

    def before_request(self, request: Any, path: str) -> tuple[Any, str]:
        request.headers["X-Session-Hook"] = "sync"
        return request, path

    def after_request(self, response: Response) -> Response:
        self.after_called = True
        return response

    @get("/echo/{resource}")
    def validated(
        self,
        resource: Annotated[str, Path],
        value: Annotated[str, Query],
        response: Response,
        limit: Annotated[int, Query] = 10,
    ) -> dict[str, Any]:
        return response.json()

    @get("/echo")
    def direct(self, response: Response) -> dict[str, Any]:
        self.function_called = True
        return response.json()

    @get("/echo")
    def hooked(self, response: Response) -> dict[str, Any]:
        return response


@SyncLifecycleAPI.validated.validation("value")
def _sync_normalize_value(session: SyncLifecycleAPI, value: str) -> str:
    return value.strip().upper()


@SyncLifecycleAPI.hooked.before_hook
def _sync_request_before_hook(
    session: SyncLifecycleAPI, request: Any, path: str
) -> tuple[Any, str]:
    request.headers["X-Request-Hook"] = "sync"
    return request, path


@SyncLifecycleAPI.hooked.after_hook
def _sync_request_after_hook(
    session: SyncLifecycleAPI, response: Response
) -> dict[str, Any]:
    payload = response.json()
    payload["request_after"] = "sync"
    return payload


class AsyncIsolationAPI(AsyncSession):
    @get("/echo/{resource}")
    async def isolated(
        self,
        resource: Annotated[str, Path],
        value: Annotated[str, Query],
        marker: Annotated[str, Header.custom_name("X-Marker")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


class SyncIsolationAPI(Session):
    @get("/echo/{resource}")
    def isolated(
        self,
        resource: Annotated[str, Path],
        value: Annotated[str, Query],
        marker: Annotated[str, Header.custom_name("X-Marker")],
        response: Response,
    ) -> dict[str, Any]:
        return response.json()


def _header(payload: dict[str, Any], name: str) -> str | None:
    return {key.lower(): value for key, value in payload["headers"].items()}.get(
        name.lower()
    )


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_validation_and_request_session_hooks(
    backend: type, base_url: str
) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any], bool]:
        async with AsyncLifecycleAPI(base_url, backend) as api:
            validated = await api.validated(resource="validated", value=" value ")
            hooked = await api.hooked()
            return validated, hooked, api.after_called

    validated, hooked, after_called = asyncio.run(run())
    assert validated["path"] == "/echo/validated"
    assert validated["query"] == {"value": ["VALUE"], "limit": ["10"]}
    assert _header(hooked, "X-Session-Hook") == "async"
    assert _header(hooked, "X-Request-Hook") == "async"
    assert hooked["request_after"] == "async"
    assert after_called is True


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_validation_and_request_session_hooks(
    backend: type, base_url: str
) -> None:
    with SyncLifecycleAPI(base_url, backend) as api:
        validated = api.validated(resource="validated", value=" value ")
        hooked = api.hooked()
        after_called = api.after_called

    assert validated["path"] == "/echo/validated"
    assert validated["query"] == {"value": ["VALUE"], "limit": ["10"]}
    assert _header(hooked, "X-Session-Hook") == "sync"
    assert _header(hooked, "X-Request-Hook") == "sync"
    assert hooked["request_after"] == "sync"
    assert after_called is True


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_direct_response_skips_function_and_can_close(
    backend: type, base_url: str
) -> None:
    async def run() -> tuple[Response, bool]:
        async with AsyncLifecycleAPI(base_url, backend, directly_response=True) as api:
            response = await api.direct()
            called = api.function_called
            if inspect.iscoroutinefunction(BACKEND_BY_SESSION[backend].response_close):
                await response.async_close()
            else:
                response.close()
            return response, called

    response, function_called = asyncio.run(run())
    assert response.json()["method"] == "GET"
    assert function_called is False
    assert response.closed is True


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_direct_response_skips_function_and_can_close(
    backend: type, base_url: str
) -> None:
    with SyncLifecycleAPI(base_url, backend, directly_response=True) as api:
        response = api.direct()
        function_called = api.function_called
        response.close()

    assert response.json()["method"] == "GET"
    assert function_called is False
    assert response.closed is True


def _assert_isolated(
    payload: dict[str, Any], resource: str, value: str, marker: str
) -> None:
    assert payload["path"] == f"/echo/{resource}"
    assert payload["query"] == {"value": [value]}
    assert _header(payload, "X-Marker") == marker


@pytest.mark.integration
@pytest.mark.parametrize("backend", ASYNC_BACKENDS, ids=ASYNC_BACKEND_IDS)
def test_async_concurrent_calls_keep_request_state_isolated(
    backend: type, base_url: str
) -> None:
    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        async with AsyncIsolationAPI(base_url, backend) as api:
            first, second = await asyncio.gather(
                api.isolated("first", "one", "first-marker"),
                api.isolated("second", "two", "second-marker"),
            )
            return first, second

    first, second = asyncio.run(run())
    _assert_isolated(first, "first", "one", "first-marker")
    _assert_isolated(second, "second", "two", "second-marker")


@pytest.mark.integration
@pytest.mark.parametrize("backend", SYNC_BACKENDS, ids=SYNC_BACKEND_IDS)
def test_sync_sequential_calls_keep_request_state_isolated(
    backend: type, base_url: str
) -> None:
    with SyncIsolationAPI(base_url, backend) as api:
        first = api.isolated("first", "one", "first-marker")
        second = api.isolated("second", "two", "second-marker")

    _assert_isolated(first, "first", "one", "first-marker")
    _assert_isolated(second, "second", "two", "second-marker")
