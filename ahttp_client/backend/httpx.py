import copy
import httpx

from typing import TYPE_CHECKING, Collection
from .base import AsyncBackend, BaseBackend, SyncBackend

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from .. import RequestCore


class CommonHttpXBackend(BaseBackend):
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

    def response_status(self, response_obj: httpx.Response) -> int:
        return response_obj.status_code

    def response_headers(self, response_obj: httpx.Response) -> dict[str, Any]:
        return dict(response_obj.headers)

    def response_url(self, response_obj: httpx.Response) -> str:
        return str(response_obj.url)

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


class HttpXAsyncSession(AsyncBackend, CommonHttpXBackend):
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
