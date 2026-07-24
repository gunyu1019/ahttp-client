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
    retry_unsafe=False,
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
    retry_unsafe=False,
)


async def async_factory() -> tuple[Response, str]:
    raise RuntimeError


def sync_factory() -> tuple[Response, str]:
    raise RuntimeError


async def use_config() -> None:
    async_result: tuple[Response, Any] = await config.execute_async(async_factory)
    sync_result: tuple[Response, Any] = config.execute_sync(sync_factory)
    print(async_core, sync_core, async_result, sync_result)
