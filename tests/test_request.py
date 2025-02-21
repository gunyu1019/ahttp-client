from typing import Annotated

import aiohttp
import pytest

from ahttp_client import *


@pytest.fixture
def test_method():
    @request("GET", "/{test_path}")
    async def test_request(
        session: Session,
        test_path: Annotated[str, Path] = "TEST_PATH",
        parameter: Annotated[str, Query] = "TEST_QUERY",
        header: Annotated[str, Header] = "TEST_HEADER",
    ) -> aiohttp.ClientResponse:
        pass

    return test_request


@pytest.fixture
def test_method_for_private_parameter():
    @Session.single_session("https://test_base_url")
    @request("GET", "/")
    @Header.default_header("private_header", "__PRIVATE_HEADER__")
    @Query.default_query("private_query", "__PRIVATE_QUERY__")
    async def test_request(session: Session) -> None:
        pass

    return test_request


def test_copy_and_equal(test_method):
    other_method = test_method.copy()
    assert other_method == test_method

    bound_argument = test_method._signature.bind(test_method.session)
    bound_argument.apply_defaults()

    other_method._fill_parameter(bound_argument)
    assert other_method != test_method


def test_fill_parameter(test_method):
    new_method = test_method.copy()

    assert "header" in new_method.header_parameter.keys()
    assert "parameter" in new_method.query_parameter.keys()

    assert "header" not in new_method.headers.keys()
    assert "parameter" not in new_method.params.keys()

    bound_argument = test_method._signature.bind(test_method.session)
    bound_argument.apply_defaults()

    new_method._fill_parameter(bound_argument)
    assert "header" in new_method.headers.keys()
    assert "parameter" in new_method.params.keys()
    assert new_method.headers["header"] == "TEST_HEADER"
    assert new_method.params["parameter"] == "TEST_QUERY"


def test_formatted_path(test_method):
    new_method = test_method.copy()

    assert "test_path" in new_method.path_parameter.keys()

    bound_argument = test_method._signature.bind(test_method.session)
    bound_argument.apply_defaults()

    formatted_path = new_method._get_request_path(bound_argument)
    assert formatted_path == "/TEST_PATH"


def test_private_component(test_method_for_private_parameter):
    assert "private_header" in test_method_for_private_parameter.headers
    assert "private_query" in test_method_for_private_parameter.params

    assert test_method_for_private_parameter.headers.get("private_header") == "__PRIVATE_HEADER__"
    assert test_method_for_private_parameter.params.get("private_query") == "__PRIVATE_QUERY__"
