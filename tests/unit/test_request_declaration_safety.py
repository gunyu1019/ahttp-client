"""MIT License

Copyright (c) 2023-present gunyu1019

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

from __future__ import annotations

from typing import Annotated

import pytest

from ahttp_client import BodyJson, Header, Path, Query, get, post


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (Query.custom_name("same"), "query"),
        (Header.custom_name("same"), "header"),
        (BodyJson.custom_name("same"), "JSON body"),
    ],
)
def test_duplicate_transmitted_component_names_are_rejected(
    component: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=f"Duplicate transmitted {message} name"):

        @post("/")
        async def endpoint(
            self: object,
            first: Annotated[str, component],
            second: Annotated[str, component],
        ) -> None:
            pass


def test_missing_path_parameter_is_rejected_at_declaration() -> None:
    with pytest.raises(ValueError, match=r"missing Path parameter\(s\): user_id"):

        @get("/users/{user_id}")
        async def endpoint(self: object) -> None:
            pass


def test_unused_path_parameter_is_rejected_at_declaration() -> None:
    with pytest.raises(ValueError, match=r"unused Path parameter\(s\): user_id"):

        @get("/users")
        async def endpoint(
            self: object,
            user_id: Annotated[int, Path],
        ) -> None:
            pass


def test_unsupported_automatic_deserialization_is_rejected() -> None:
    class UnsupportedModel:
        pass

    with pytest.raises(TypeError, match="No deserializer is registered"):

        @get("/", directly_response=True)
        async def endpoint(self: object) -> UnsupportedModel:
            ...
