from __future__ import annotations

import aiohttp
import copy
import json as jsonlib

from typing import Collection, TYPE_CHECKING
from .base import BaseBackend, AsyncBackendSession

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from .. import RequestCore


class AiohttpBackend(BaseBackend):
    @property
    def response_cls(self) -> type[Any]:
        return aiohttp.ClientResponse

    async def response_data(self, response_obj: aiohttp.ClientResponse) -> bytes:
        return await response_obj.read()

    async def response_text(self, response_obj: aiohttp.ClientResponse) -> str:
        return await response_obj.text()

    async def response_json(
            self, response_obj: aiohttp.ClientResponse,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        if json_parser is None:
            json_parser = jsonlib.loads

        if json_kwargs is None:
            return await response_obj.json(loads=json_parser)
        raw_response = await response_obj.text()
        if not raw_response:
            return None
        return json_parser(loads=json_parser, **json_kwargs)

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


class AiohttpSession(aiohttp.ClientSession, AsyncBackendSession):
    async def wrapped_close(self):
        await self.close()

    async def wrapped_request(self, method: str, path: str, **kwargs):
        return await self.request(method, path, **kwargs)

    async def wrapped_get(self, path: str, **kwargs):
        return await self.get(path, **kwargs)

    async def wrapped_post(self, path: str, **kwargs):
        return await self.post(path, **kwargs)

    async def wrapped_options(self, path: str, **kwargs):
        return await self.options(path, **kwargs)

    async def wrapped_delete(self, path: str, **kwargs):
        return await self.delete(path, **kwargs)

    async def wrapped_patch(self, path: str, **kwargs):
        return await self.patch(path, **kwargs)

    async def wrapped_put(self, path: str, **kwargs):
        return await self.put(path, **kwargs)
