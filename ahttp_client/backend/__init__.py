from .base import BaseBackend, AsyncBackend, SyncBackend

__all__ = ["BaseBackend", "AsyncBackend", "SyncBackend"]

try:
    from .aiohttp import AiohttpBackend
except ModuleNotFoundError as exc:
    if exc.name != "aiohttp":
        raise
else:
    AiohttpSession = AiohttpBackend  # backward-compatible alias
    __all__ += ["AiohttpBackend", "AiohttpSession"]

try:
    from .httpx import HttpXAsyncSession, HttpXSyncSession
except ModuleNotFoundError as exc:
    if exc.name != "httpx":
        raise
else:
    __all__ += ["HttpXAsyncSession", "HttpXSyncSession"]

try:
    from .requests import RequestsBackend
except ModuleNotFoundError as exc:
    if exc.name != "requests":
        raise
else:
    RequestSession = RequestsBackend  # backward-compatible alias
    __all__ += ["RequestsBackend", "RequestSession"]
