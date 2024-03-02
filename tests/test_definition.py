import copy
import inspect
import aiohttp
import pytest

from typing import Annotated, Any

from async_client_decorator import *
from async_client_decorator.request import RequestCore


@pytest.fixture
def test_method_with_parameter():
    @Session.single_session("https://test_base_url")
    @request("GET", "/{test_path}")
    async def test_request(
        session: Session,
        test_response: aiohttp.ClientResponse,
        test_path: str | Path = "__TEST_PATH__",
        test_query: str | Query = "__TEST_PARAMETER__",
        test_header: str | Header = "__TEST_HEADER__",
        test_body: dict | Body = None,
    ) -> aiohttp.ClientResponse:
        pass

    return test_request


@pytest.fixture
def test_method_with_annotated():
    @Session.single_session("https://test_base_url")
    @request("GET", "/{test_path}")
    async def test_request(
        session: Session,
        test_path: Annotated[str, Path],
        test_query: Annotated[str, Query],
        test_header: Annotated[str, Header],
        test_body: Annotated[dict, Body],
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_with_decorator_parameter():
    @Session.single_session("https://test_base_url")
    @request(
        "GET",
        "/{test_path}",
        path_parameter=["test_path"],
        query_parameter=["test_query"],
        header_parameter=["test_header"],
        body_parameter="test_body",
    )
    async def test_request(
        session: Session,
        test_path: str,
        test_query: str,
        test_header: str,
        test_body: aiohttp.FormData = None,
    ) -> None:
        pass

    return test_request


def test_component_parameter_1(test_method_with_parameter):
    assert "test_header" in test_method_with_parameter.header_parameter
    assert "test_query" in test_method_with_parameter.query_parameter
    assert "test_path" in test_method_with_parameter.path_parameter
    assert "test_response" in test_method_with_parameter.response_parameter

    assert test_method_with_parameter.body_parameter.name == "test_body"
    assert test_method_with_parameter.body_parameter_type == "json"


def test_component_parameter_2(test_method_with_decorator_parameter):
    assert "test_header" in test_method_with_decorator_parameter.header_parameter
    assert "test_query" in test_method_with_decorator_parameter.query_parameter
    assert "test_path" in test_method_with_decorator_parameter.path_parameter

    assert test_method_with_decorator_parameter.body_parameter.name == "test_body"
    assert test_method_with_decorator_parameter.body_parameter_type == "data"


def test_component_parameter_3(test_method_with_annotated):
    assert "test_header" in test_method_with_annotated.header_parameter
    assert "test_query" in test_method_with_annotated.query_parameter
    assert "test_path" in test_method_with_annotated.path_parameter

    assert test_method_with_annotated.body_parameter.name == "test_body"
    assert test_method_with_annotated.body_parameter_type == "json"
