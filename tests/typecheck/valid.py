from __future__ import annotations

from typing import Any

from ahttp_client import retry
from ahttp_client.exception import HTTPClientError, HTTPServerError
from ahttp_client.request import AsyncRequestCore, SyncRequestCore, request
from ahttp_client.response import Response
from ahttp_client.retry import RetryConfig


@retry()
@request("GET", "/async")
async def async_endpoint(session: Any) -> None:
    pass


@request("GET", "/sync")
@retry(
    5,
    backoff_factor=0.5,
    retry_on=(HTTPServerError, HTTPClientError),
    max_delay=4.0,
)
def sync_endpoint(session: Any) -> None:
    pass


async_core: AsyncRequestCore = async_endpoint
sync_core: SyncRequestCore = sync_endpoint
config = RetryConfig(
    max_retries=3,
    backoff_factor=1.0,
    retry_on=(OSError,),
    max_delay=None,
)


async def async_factory() -> tuple[Response, str]:
    raise RuntimeError


def sync_factory() -> tuple[Response, str]:
    raise RuntimeError


async def use_config() -> None:
    async_result: tuple[Response, Any] = await config.execute_async(async_factory)
    sync_result: tuple[Response, Any] = config.execute_sync(sync_factory)
    print(async_core, sync_core, async_result, sync_result)
