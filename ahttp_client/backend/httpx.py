import copy
import httpx

from typing import TYPE_CHECKING, Collection
from .base import AsyncBackendSession, BaseBackend, SyncBackendSession

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from .. import RequestCore


class HttpXBackend(BaseBackend):
    @property
    def response_cls(self) -> type[Any]:
        return httpx.Response

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

            if body_type is None:
                body_type = (
                    "json" if isinstance(request_obj.body, Collection)
                    else "data"
                )
            request_kwargs[body_type] = body

        return request_kwargs

    def response_data(self, response_obj: httpx.Response) -> bytes:
        return response_obj.content

    def response_text(self, response_obj: httpx.Response) -> str:
        return response_obj.text

    def response_json(
            self, response_obj: httpx.Response,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Optional[Any]:
        if json_parser is None:
            return response_obj.json(**json_kwargs)
        raw_response = response_obj.content
        if not raw_response:
            return None
        return json_parser(raw_response, **json_kwargs)


class HttpXAsyncSession(httpx.AsyncClient, AsyncBackendSession):
    async def wrapped_close(self):
        await self.aclose()

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


class HttpXSyncSession(httpx.Client, SyncBackendSession):
    def wrapped_close(self):
        self.close()

    def wrapped_request(self, method: str, path: str, **kwargs):
        return self.request(method, path, **kwargs)

    def wrapped_get(self, path: str, **kwargs):
        return self.get(path, **kwargs)

    def wrapped_post(self, path: str, **kwargs):
        return self.post(path, **kwargs)

    def wrapped_options(self, path: str, **kwargs):
        return self.options(path, **kwargs)

    def wrapped_delete(self, path: str, **kwargs):
        return self.delete(path, **kwargs)

    def wrapped_patch(self, path: str, **kwargs):
        return self.patch(path, **kwargs)

    def wrapped_put(self, path: str, **kwargs):
        return self.put(path, **kwargs)
