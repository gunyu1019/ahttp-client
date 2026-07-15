from .base import BaseBackend, AsyncBackend, SyncBackend

try:
    from .aiohttp import AiohttpBackend

    AiohttpSession = AiohttpBackend
except ImportError:
    pass

try:
    from .httpx import HttpXAsyncSession, HttpXSyncSession
except ImportError:
    pass

try:
    from .requests import RequestsBackend

    RequestSession = RequestsBackend
except ImportError:
    pass
