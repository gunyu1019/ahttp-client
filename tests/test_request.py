from typing import Annotated

import aiohttp
import pytest

from async_client_decorator import *


@pytest.fixture
def test_method():
    @request("GET", "/{test_path}")
    async def test_request(
        session: Session,
        parameter: Annotated[str, Query] = "TEST_QUERY",
        header: Annotated[str, Header] = "TEST_HEADER",
    ) -> aiohttp.ClientResponse:
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

    assert "header" not in new_method.headers.keys()
    assert "parameter" not in new_method.params.keys()

    bound_argument = test_method._signature.bind(test_method.session)
    bound_argument.apply_defaults()

    new_method._fill_parameter(bound_argument)
    assert "header" in new_method.headers.keys()
    assert "parameter" in new_method.params.keys()
    assert new_method.headers["header"] == "TEST_HEADER"
    assert new_method.params["parameter"] == "TEST_QUERY"
