"""MIT License

Copyright (c) 2023 gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import aiohttp
import dataclasses
import inspect

from typing import Any, Optional, Literal


@dataclasses.dataclass
class Component:
    header: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    query: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    form: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    path: dict[str, inspect.Parameter | Any] = dataclasses.field(default_factory=dict)
    body: Optional[inspect.Parameter | dict | list | aiohttp.FormData] = None
    body_type: str = None
    response: list[str] = dataclasses.field(default_factory=list)

    def fill_keyword_argument_to_component(
        self, key_type: Literal["header", "query", "form", "path"], kwargs
    ) -> dict[str, Any]:
        data: dict[str, Any] = getattr(self, key_type)
        for key, value in data.items():
            if isinstance(value, inspect.Parameter):
                argument = self.fill_keyword_argument(key, value, kwargs)
                if inspect._empty == argument:
                    raise TypeError(
                        f"request function missing 1 required positional argument: '{key}'"
                    )
                data[key] = argument
        setattr(self, key_type, data)
        return data

    @staticmethod
    def fill_keyword_argument(
        key: str, parameter: inspect.Parameter, kwargs: dict[str, Any]
    ):
        return kwargs.get(key) if key in kwargs.keys() else parameter.default

    def set_body(self, data: inspect.Parameter | dict | list | aiohttp.FormData):
        body_annotations = (
            data.annotation if isinstance(data, inspect.Parameter) else type(data)
        )

        if not (
            issubclass(dict, body_annotations)
            or issubclass(list, body_annotations)
            or issubclass(aiohttp.FormData, body_annotations)
        ):
            raise TypeError(
                "Body parameter can only have aiohttp.FormData or dict, list."
            )

        if self.body is not None:
            raise ValueError("Only one Body Parameter is allowed.")

        if issubclass(aiohttp.FormData, body_annotations):
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
