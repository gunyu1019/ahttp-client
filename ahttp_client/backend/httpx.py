from __future__ import annotations

import copy
import io
import httpx

from abc import ABC
from typing import TYPE_CHECKING
from .base import AsyncBackend, BaseBackend, SyncBackend
from ..enum import BodyType

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from ..request import RequestCore


class CommonHttpXBackend(BaseBackend, ABC):
    response_cls = httpx.Response
    native_base_url = True

    def get_request_kwargs(self, request_obj: RequestCore) -> dict[str, Any]:
        request_kwargs = copy.deepcopy(request_obj.request_kwargs)
        if len(request_obj.headers) > 0:
            request_kwargs["headers"] = request_obj.headers
        if len(request_obj.params) > 0:
            request_kwargs["params"] = request_obj.params

        if request_obj.is_body:
            body_type = request_obj.body_type
            if body_type == BodyType.JSON:
                request_kwargs["json"] = request_obj.body
            elif body_type == BodyType.URL_ENCODED:
                request_kwargs["data"] = request_obj.body
            elif body_type == BodyType.FORM_DATA:
                files = {
                    k: (None, v if isinstance(v, (str, bytes)) else str(v))
                    for k, v in (request_obj.body or {}).items()
                }
                files.update(request_obj._body_file or {})
                request_kwargs["files"] = files
            elif body_type == BodyType.RAW:
                body = request_obj.body
                if isinstance(body, io.IOBase):
                    request_kwargs["content"] = body.read()
                else:
                    request_kwargs["content"] = body
        return request_kwargs

    def response_status(self, response_obj: httpx.Response) -> int:
        return response_obj.status_code

    def response_headers(self, response_obj: httpx.Response) -> dict[str, Any]:
        return dict(response_obj.headers)

    def response_url(self, response_obj: httpx.Response) -> str:
        return str(response_obj.url)

    def response_closed(self, response_obj: httpx.Response) -> bool:
        return response_obj.is_closed

    def response_data(self, response_obj: httpx.Response) -> bytes:
        return response_obj.content

    def response_text(self, response_obj: httpx.Response) -> str:
        return response_obj.text

    def response_json(
        self,
        response_obj: httpx.Response,
        json_parser: Optional[Callable[..., Any]] = None,
        json_kwargs: Optional[dict[str, Any]] = None,
    ) -> Optional[Any]:
        json_kwargs = json_kwargs or dict()
        if json_parser is None:
            return response_obj.json(**json_kwargs)
        raw_response = response_obj.content
        if not raw_response:
            return None
        return json_parser(raw_response, **json_kwargs)


class HttpXAsyncSession(AsyncBackend, CommonHttpXBackend):
    session_cls = httpx.AsyncClient

    @property
    def session_closed(self) -> bool:
        return self.session.is_closed

    async def response_close(self, response_obj: httpx.Response) -> None:
        await response_obj.aclose()

    async def session_close(self):
        await self.session.aclose()

    async def session_request(self, method: str, path: str, **kwargs):
        return await self.session.request(method, path, **kwargs)

    async def session_get(self, path: str, **kwargs):
        return await self.session.get(path, **kwargs)

    async def session_post(self, path: str, **kwargs):
        return await self.session.post(path, **kwargs)

    async def session_options(self, path: str, **kwargs):
        return await self.session.options(path, **kwargs)

    async def session_delete(self, path: str, **kwargs):
        return await self.session.delete(path, **kwargs)

    async def session_patch(self, path: str, **kwargs):
        return await self.session.patch(path, **kwargs)

    async def session_put(self, path: str, **kwargs):
        return await self.session.put(path, **kwargs)


class HttpXSyncSession(SyncBackend, CommonHttpXBackend):
    session_cls = httpx.Client

    def response_close(self, response_obj: httpx.Response) -> None:
        response_obj.close()

    @property
    def session_closed(self) -> bool:
        return self.session.is_closed

    def session_close(self):
        self.session.close()

    def session_request(self, method: str, path: str, **kwargs):
        return self.session.request(method, path, **kwargs)

    def session_get(self, path: str, **kwargs):
        return self.session.get(path, **kwargs)

    def session_post(self, path: str, **kwargs):
        return self.session.post(path, **kwargs)

    def session_options(self, path: str, **kwargs):
        return self.session.options(path, **kwargs)

    def session_delete(self, path: str, **kwargs):
        return self.session.delete(path, **kwargs)

    def session_patch(self, path: str, **kwargs):
        return self.session.patch(path, **kwargs)

    def session_put(self, path: str, **kwargs):
        return self.session.put(path, **kwargs)
