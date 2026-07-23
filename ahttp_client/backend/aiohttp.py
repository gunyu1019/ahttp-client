from __future__ import annotations

import aiohttp
import copy
import io
import json as jsonlib

from typing import TYPE_CHECKING
from .base import AsyncBackend
from ..enum import BodyType

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from ..request import RequestCore


class AiohttpBackend(AsyncBackend):
    """Backend adapter for :class:`aiohttp.ClientSession`.

    Requires the ``aiohttp`` package (``pip install aiohttp``). Registered
    for ``aiohttp.ClientSession`` and wraps ``aiohttp.ClientResponse`` as
    its response type.
    """

    session_cls = aiohttp.ClientSession
    response_cls = aiohttp.ClientResponse
    native_base_url = True
    session: aiohttp.ClientSession

    async def pre_read_response(self, response_obj: aiohttp.ClientResponse) -> None:
        await response_obj.read()

    def response_data(self, response_obj: aiohttp.ClientResponse) -> bytes:
        return getattr(response_obj, "_body", b"")

    def response_text(self, response_obj: aiohttp.ClientResponse) -> str:
        body = getattr(response_obj, "_body", b"")
        encoding = response_obj.get_encoding()
        return body.decode(encoding)

    def response_json(
        self,
        response_obj: aiohttp.ClientResponse,
        json_parser: Optional[Callable[..., Any]] = None,
        json_kwargs: Optional[dict[str, Any]] = None,
    ) -> Optional[Any]:
        body = getattr(response_obj, "_body", b"")
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

    def response_closed(self, response_obj: aiohttp.ClientResponse) -> bool:
        return response_obj.closed

    @property
    def session_closed(self) -> bool:
        return bool(self.session.closed)

    def get_request_kwargs(self, request_obj: RequestCore[Any, Any]) -> dict[str, Any]:
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
                # Keep non-ASCII multipart field names and filenames intact.
                # aiohttp's default ``quote_fields=True`` percent-encodes them,
                # which makes a filename such as "한글.txt" arrive at the server
                # as its literal percent-encoded representation.
                data = aiohttp.FormData(quote_fields=False)
                if request_obj.body is not None:
                    for key, value in request_obj.body.items():
                        data.add_field(
                            key,
                            value if isinstance(value, (str, bytes)) else str(value),
                            content_type="text/plain",
                        )

                if request_obj._body_file is not None:
                    for key, (
                        file_name,
                        value,
                        content_type,
                    ) in request_obj._body_file.items():
                        data.add_field(key, value, filename=file_name, content_type=content_type)

                request_kwargs["data"] = data
            elif body_type == BodyType.RAW:
                request_kwargs["data"] = request_obj.body
        return request_kwargs

    async def session_close(self) -> None:
        await self.session.close()

    async def session_request(self, method: str, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.request(method, path, **kwargs)

    async def session_get(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.get(path, **kwargs)

    async def session_post(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.post(path, **kwargs)

    async def session_options(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.options(path, **kwargs)

    async def session_delete(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.delete(path, **kwargs)

    async def session_patch(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.patch(path, **kwargs)

    async def session_put(self, path: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.session.put(path, **kwargs)
