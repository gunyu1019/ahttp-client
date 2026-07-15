from __future__ import annotations

import copy
import io
import requests
from typing import TYPE_CHECKING

from .base import SyncBackend
from ..enum import BodyType

if TYPE_CHECKING:
    from typing import Any, Optional, Callable
    from ..request import RequestCore


class RequestsBackend(SyncBackend):
    session_cls = requests.Session
    response_cls = requests.Response

    def __init__(self, session: type, **kwargs: Any):
        super(RequestsBackend, self).__init__(session, **kwargs)
        self._closed = False

    def response_data(self, response_obj: requests.Response) -> bytes:
        return response_obj.content

    def response_text(self, response_obj: requests.Response) -> str:
        return response_obj.text

    def response_json(
        self,
        response_obj: requests.Response,
        json_parser: Optional[Callable[..., Any]] = None,
        json_kwargs: Optional[dict[str, Any]] = None,
    ) -> Optional[Any]:
        if not response_obj.content:
            return None

        json_kwargs = json_kwargs or dict()
        if json_parser is not None:
            return json_parser(response_obj.text, **json_kwargs)
        return response_obj.json(**json_kwargs)

    def response_status(self, response_obj: requests.Response) -> int:
        return response_obj.status_code

    def response_headers(self, response_obj: requests.Response) -> dict[str, Any]:
        return dict(response_obj.headers)

    def response_url(self, response_obj: requests.Response) -> str:
        return response_obj.url

    def response_close(self, response_obj: requests.Response) -> None:
        response_obj.close()

    def response_closed(self, response_obj: requests.Response) -> Optional[bool]:
        return None

    @property
    def session_closed(self) -> bool:
        return self._closed

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
                request_kwargs["data"] = request_obj.body
        return request_kwargs

    def session_close(self):
        self.session.close()
        self._closed = True

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
