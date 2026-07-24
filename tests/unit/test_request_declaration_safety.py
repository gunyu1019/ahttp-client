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
