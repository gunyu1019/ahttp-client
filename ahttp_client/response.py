from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional
    from .backend.base import BaseBackend


class Response:
    def __init__(self, response_obj: Any, backend: BaseBackend):
        self._raw_response_obj = response_obj
        self._backend = backend

    @property
    def raw(self) -> Any:
        return self._raw_response_obj

    @property
    def session(self) -> Any:
        return self._backend.session

    @property
    def header(self) -> dict[str, Any]:
        return self._backend.response_headers(self._raw_response_obj)

    @property
    def status(self) -> int:
        return self._backend.response_status(self._raw_response_obj)

    @property
    def url(self) -> str:
        return self._backend.response_url(self._raw_response_obj)

    def close(self) -> None:
        self._backend.response_close(self._raw_response_obj)

    def text(self) -> str:
        return self._backend.response_text(self._raw_response_obj)

    def json(
            self,
            json_parser: Optional[Callable[[Any, ...], Any]] = None,
            json_kwargs: Optional[dict[str, Any]] = None
    ) -> Any:
        return self._backend.response_json(self._raw_response_obj, json_parser, json_kwargs)

    def content(self) -> bytes:
        return self._backend.response_data(self._raw_response_obj)
