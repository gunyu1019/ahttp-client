import aiohttp
import dataclasses
import inspect

from typing import Any, Optional, Literal


@dataclasses.dataclass
class Component:
    header: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    query: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    form: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    body: Optional[inspect.Parameter | dict | list | aiohttp.FormData] = None
    body_type: Literal["json", "data"] = None
    response: list[str] = dataclasses.field(default_factory=list)

    def fill_keyword_argument_to_component(
        self, key_type: Literal["header", "query", "form"], kwargs
    ) -> dict[str, Any]:
        data: dict[str, Any] = getattr(self, key_type)
        for key, value in data.items():
            if isinstance(value, inspect.Parameter):
                data[key] = self.fill_keyword_argument(key, value, kwargs)
        setattr(self, key_type, data)
        return data

    @staticmethod
    def fill_keyword_argument(
        key: str, parameter: inspect.Parameter, kwargs: dict[str, Any]
    ):
        return kwargs.get(key) if key in kwargs.keys() else parameter.default

    def set_body(self, data: inspect.Parameter |     dict | list | aiohttp.FormData):
        body_annotations = (
            data.annotation if isinstance(data, inspect.Parameter) else type(data)
        )
        if not issubclass(
            body_annotations,
            (
                dict,
                list,
                aiohttp.FormData,
            ),
        ):
            raise TypeError(
                "Body parameter can only have aiohttp.FormData or dict, list."
            )

        if self.body is not None:
            raise ValueError("Only one Body Parameter is allowed.")

        if issubclass(body_annotations, aiohttp.FormData):
            self.body_type = "data"
        else:
            self.body_type = "json"
        self.body = data
        self._duplicated_check_body()

    def add_form(self, key: str, value: inspect.Parameter | Any):
        if self.body_type is None:
            self.body_type = "data"
        self.form[key] = value
        self._duplicated_check_body()

    def get_form(self) -> aiohttp.FormData:
        data = aiohttp.FormData()
        for key, value in self.form.items():
            data.add_field(key, value)
        return data

    def get_body(self) -> aiohttp.FormData | dict | list:
        if self.body_type == "data" and len(self.form) > 0:
            return self.get_form()
        return self.body

    def is_formal_form(self) -> bool:
        return len(self.form) > 0

    def is_body(self):
        return self.body_type is not None

    def _duplicated_check_body(self):
        if self.body is not None and len(self.form) > 0:
            raise ValueError("Use only one Form Parameter or Body Parameter.")