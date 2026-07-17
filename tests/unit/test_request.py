import io
from typing import Annotated, get_type_hints

import pytest

from ahttp_client import (
    BaseSession,
    Header,
    Path,
    Query,
    request,
)
from ahttp_client.enum import DirectResponseType
from ahttp_client.request import RequestCore


@pytest.fixture
def test_method():
    @request("GET", "/{test_path}")
    async def test_request(
        session: BaseSession,
        test_path: Annotated[str, Path] = "TEST_PATH",
        parameter: Annotated[str, Query] = "TEST_QUERY",
        header: Annotated[str, Header] = "TEST_HEADER",
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_for_private_parameter():
    @request("GET", "/")
    @Header.default_header("private_header", "__PRIVATE_HEADER__")
    @Query.default_query("private_query", "__PRIVATE_QUERY__")
    async def test_request(session: BaseSession) -> None:
        pass

    return test_request


def test_copy_and_equal(test_method):
    other_method = test_method.copy()
    assert other_method == test_method

    bound_argument = test_method._signature.bind(None)
    bound_argument.apply_defaults()

    other_method._fill_parameter(None, bound_argument)
    assert other_method != test_method


def test_copy_isolates_mutable_static_body() -> None:
    @request(
        "POST",
        "/",
        body={"profile": {"tags": ["original"]}},
    )
    def endpoint(session: BaseSession) -> None:
        pass

    first = endpoint.copy()
    second = endpoint.copy()

    first.body["profile"]["tags"].append("first")

    assert endpoint.body == {"profile": {"tags": ["original"]}}
    assert second.body == {"profile": {"tags": ["original"]}}


def test_copy_isolates_multipart_map_without_copying_file_stream() -> None:
    @request("POST", "/")
    def endpoint(session: BaseSession) -> None:
        pass

    stream = io.BytesIO(b"content")
    endpoint._body_file = {
        "document": ("document.txt", stream, "text/plain"),
    }

    copied = endpoint.copy()
    copied._body_file["extra"] = ("extra.txt", b"extra", "text/plain")

    assert "extra" not in endpoint._body_file
    assert copied._body_file["document"][1] is stream


def test_fill_parameter(test_method):
    new_method = test_method.copy()

    assert "header" in new_method.header_parameter.keys()
    assert "parameter" in new_method.query_parameter.keys()

    assert "header" not in new_method.headers.keys()
    assert "parameter" not in new_method.params.keys()

    bound_argument = test_method._signature.bind(None)
    bound_argument.apply_defaults()

    new_method._fill_parameter(None, bound_argument)
    assert "header" in new_method.headers.keys()
    assert "parameter" in new_method.params.keys()
    assert new_method.headers["header"] == "TEST_HEADER"
    assert new_method.params["parameter"] == "TEST_QUERY"


def test_formatted_path(test_method):
    new_method = test_method.copy()

    assert "test_path" in new_method.path_parameter.keys()

    bound_argument = test_method._signature.bind(None)
    bound_argument.apply_defaults()

    formatted_path = new_method._get_request_path(bound_argument)
    assert formatted_path == "/TEST_PATH"


def test_formatted_path_percent_encodes_string_segments() -> None:
    @request("GET", "/users/{user}/files/{filename}")
    def endpoint(
        session: BaseSession,
        user: Annotated[str, Path],
        filename: Annotated[str, Path],
    ) -> None:
        pass

    bound_argument = endpoint._signature.bind(
        None,
        "team/admin",
        "한 글%.txt",
    )

    assert endpoint._get_request_path(bound_argument) == ("/users/team%2Fadmin/files/%ED%95%9C%20%EA%B8%80%25.txt")


def test_formatted_path_preserves_non_string_format_specifiers() -> None:
    @request("GET", "/items/{item_id:04d}")
    def endpoint(
        session: BaseSession,
        item_id: Annotated[int, Path],
    ) -> None:
        pass

    bound_argument = endpoint._signature.bind(None, 7)

    assert endpoint._get_request_path(bound_argument) == "/items/0007"


def test_private_component(test_method_for_private_parameter):
    assert "private_header" in test_method_for_private_parameter.headers
    assert "private_query" in test_method_for_private_parameter.params

    assert test_method_for_private_parameter.headers.get("private_header") == "__PRIVATE_HEADER__"
    assert test_method_for_private_parameter.params.get("private_query") == "__PRIVATE_QUERY__"


def test_async_validator_is_rejected(test_method):
    with pytest.raises(TypeError, match="validator must not be a coroutine"):

        @test_method.validation("parameter")
        async def validate_parameter(session: BaseSession, value: str) -> str:
            return value


def test_directly_response_accepts_direct_response_type():
    assert get_type_hints(request)["directly_response"] == DirectResponseType | bool
    assert get_type_hints(RequestCore.__init__)["directly_response"] == DirectResponseType | bool

    @request("GET", "/", directly_response=DirectResponseType.RESPONSE)
    async def direct_request(session: BaseSession) -> None:
        pass

    assert direct_request.directly_response is DirectResponseType.RESPONSE
