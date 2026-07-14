from __future__ import annotations

import aiohttp
import copy
import json as jsonlib

from typing import Collection, TYPE_CHECKING
from .base import AsyncBackend

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from .. import RequestCore


class AiohttpBackend(AsyncBackend):
    session_cls = aiohttp.ClientSession
    response_cls = aiohttp.ClientResponse
    native_base_url = True

    async def pre_read_response(self, response_obj: aiohttp.ClientResponse) -> None:
        await response_obj.read()

    def response_data(self, response_obj: aiohttp.ClientResponse) -> bytes:
        return getattr(response_obj, "_body", b'')

    def response_text(self, response_obj: aiohttp.ClientResponse) -> str:
        body = getattr(response_obj, "_body", b'')
        encoding = response_obj.get_encoding()
        return body.decode(encoding)

    def response_json(
            self, response_obj: aiohttp.ClientResponse,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Optional[Any]:
        body = getattr(response_obj, "_body", b'')
        if not body:
            return None

        json_parser = json_parser or jsonlib.loads
        json_kwargs = json_kwargs or dict()
        return json_parser(body, **json_kwargs)

    def response_status(self, response_obj: aiohttp.ClientResponse) -> int:
        return response_obj.status

    def response_headers(self, response_obj: aiohttp.ClientResponse) -> dict[str, Any]:
        return dict(response_obj.headers)

    def response_url(self, response_obj: aiohttp.ClientResponse) -> str:
        return str(response_obj.url)

    def response_close(self, response_obj: aiohttp.ClientResponse) -> None:
        response_obj.close()

    @property
    def session_closed(self) -> bool:
        return self.session.closed

    def get_request_kwargs(self, request_obj: RequestCore) -> dict[str, Any]:
        request_kwargs = copy.deepcopy(request_obj.request_kwargs)

        # Header
        if len(request_obj.headers) > 0:
            request_kwargs["headers"] = request_obj.headers

        # Parameter
        if len(request_obj.params) > 0:
            request_kwargs["params"] = request_obj.params

        # Body
        if request_obj.is_body:
            body_type = str(request_obj.body_parameter_type)
            body = request_obj.body

            if body_type == "data":
                data = aiohttp.FormData()
                for key, value in body.items():
                    data.add_field(key, value)
                body = data
            elif body_type is None:
                body_type = (
                    "json" if isinstance(request_obj.body, Collection)
                    else "data"
                )
            request_kwargs[body_type] = body

        return request_kwargs

    async def session_close(self):
        await self.session.close()

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
