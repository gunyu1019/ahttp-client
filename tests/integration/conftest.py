from __future__ import annotations

import asyncio
import base64
import threading
from collections.abc import Generator, Iterable
from typing import Any

import pytest
from aiohttp import web
from aiohttp.multipart import BodyPartReader


def _multi_dict(data: Any) -> dict[str, list[str]]:
    return {key: [str(value) for value in data.getall(key)] for key in data}


async def _echo(request: web.Request) -> web.Response:
    """Return the request as JSON so tests assert data received on the wire."""
    payload: dict[str, Any] = {
        "method": request.method,
        "path": request.path,
        "query": _multi_dict(request.query),
        "headers": dict(request.headers),
        "content_type": request.content_type,
    }

    if request.content_type == "application/json":
        payload["json"] = await request.json()
    elif request.content_type == "application/x-www-form-urlencoded":
        payload["form"] = _multi_dict(await request.post())
    elif request.content_type == "multipart/form-data":
        fields: dict[str, list[str]] = {}
        files: dict[str, list[dict[str, str]]] = {}
        reader = await request.multipart()
        async for part in reader:
            if not isinstance(part, BodyPartReader) or part.name is None:
                continue
            raw = await part.read()
            if part.filename is None:
                fields.setdefault(part.name, []).append(raw.decode("utf-8"))
            else:
                files.setdefault(part.name, []).append(
                    {
                        "filename": part.filename,
                        "content_type": part.headers.get("Content-Type", ""),
                        "base64": base64.b64encode(raw).decode("ascii"),
                    }
                )
        payload["form"] = fields
        payload["files"] = files
    else:
        raw = await request.read()
        payload["raw_base64"] = base64.b64encode(raw).decode("ascii")

    return web.json_response(payload)


class EchoServer:
    """Background-loop loopback server with deterministic teardown."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._ready = threading.Event()
        self._runner: web.AppRunner | None = None
        self._error: BaseException | None = None
        self.port: int | None = None

    @property
    def base_url(self) -> str:
        if self.port is None:
            raise RuntimeError("Echo server has not started")
        return f"http://127.0.0.1:{self.port}"

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._start())
        except BaseException as exc:
            self._error = exc
            self._ready.set()
            return
        self._loop.run_forever()
        self._loop.close()

    async def _start(self) -> None:
        app = web.Application()
        app.router.add_route("*", "/echo", _echo)
        app.router.add_route("*", "/echo/{resource}", _echo)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await site.start()
        sockets: Iterable[Any] = site._server.sockets  # type: ignore[union-attr]
        self.port = next(iter(sockets)).getsockname()[1]
        self._ready.set()

    def start(self) -> "EchoServer":
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise TimeoutError("Echo server did not become ready within 10 seconds")
        if self._error is not None:
            raise RuntimeError("Echo server failed to start") from self._error
        return self

    def close(self) -> None:
        if self._runner is not None and self._loop.is_running():
            cleanup = asyncio.run_coroutine_threadsafe(self._runner.cleanup(), self._loop)
            cleanup.result(timeout=10)
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=10)


@pytest.fixture(scope="session")
def echo_server() -> Generator[EchoServer, None, None]:
    server = EchoServer().start()
    try:
        yield server
    finally:
        server.close()


@pytest.fixture(scope="session")
def base_url(echo_server: EchoServer) -> str:
    return echo_server.base_url
