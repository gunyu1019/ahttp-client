import copy
import inspect

import aiohttp
import pytest

from async_client_decorator import *
from async_client_decorator.request import _get_kwarg_for_request


@Session.single_session("https://dummy_base_url")
@request("GET", "/{dummy_path}")
async def dummy_request_1(
    session: Session,
    dummy_response: aiohttp.ClientResponse,
    dummy_path: str | Path = "__TEST_PATH__",
    dummy_query: str | Query = "__TEST_PARAMETER__",
    dummy_header: str | Header = "__TEST_HEADER__",
    dummy_body: dict | Body = None,
) -> aiohttp.ClientResponse:
    pass


@Session.single_session("https://dummy_base_url")
@request(
    "GET",
    "/{dummy_path}",
    path_parameter=["dummy_path"],
    query_parameter=["dummy_query"],
    header_parameter=["dummy_header"],
    body_parameter="dummy_body",
)
async def dummy_request_2(
    session: Session,
    dummy_path: str,
    dummy_query: str,
    dummy_header: str,
    dummy_body: aiohttp.FormData = None,
) -> None:
    pass


@Session.single_session("https://dummy_base_url")
@request("GET", "/")
@Form.default_form("private_form", "__PRIVATE_FORM__")
@Header.default_header("private_header", "__PRIVATE_HEADER__")
@Path.default_path("private_path", "__PRIVATE_PATH__")
@Query.default_query("private_query", "__PRIVATE_QUERY__")
async def dummy_request_3(session: Session) -> None:
    pass


def test_component_parameter_1():
    assert "dummy_header" in dummy_request_1.__component_parameter__.header
    assert "dummy_query" in dummy_request_1.__component_parameter__.query
    assert "dummy_path" in dummy_request_1.__component_parameter__.path
    assert "dummy_response" in dummy_request_1.__component_parameter__.response

    assert dummy_request_1.__component_parameter__.body.name == "dummy_body"
    assert dummy_request_1.__component_parameter__.body_type == "json"


def test_component_parameter_2():
    assert "dummy_header" in dummy_request_2.__component_parameter__.header
    assert "dummy_query" in dummy_request_2.__component_parameter__.query
    assert "dummy_path" in dummy_request_2.__component_parameter__.path

    assert dummy_request_2.__component_parameter__.body.name == "dummy_body"
    assert dummy_request_2.__component_parameter__.body_type == "data"


def test_fill_keyword():
    kwargs = {
        "dummy_header": "DUMMY_HEADER",
        "dummy_path": "DUMMY_PATH",
        "dummy_query": "DUMMY_QUERY",
    }
    component = dummy_request_1.__component_parameter__
    wrapped_component = copy.deepcopy(component)
    path, request_kwargs = _get_kwarg_for_request(
        wrapped_component, dummy_request_1.__request_path__, {}, kwargs
    )

    signature = inspect.signature(dummy_request_1)
    parameter = signature.parameters

    assert path == "/DUMMY_PATH"
    assert request_kwargs["headers"]["dummy_header"] == kwargs.get("dummy_header")
    assert request_kwargs["params"]["dummy_query"] == kwargs.get("dummy_query")


def test_fill_keyword_default():
    component = dummy_request_1.__component_parameter__
    wrapped_component = copy.deepcopy(component)
    path, request_kwargs = _get_kwarg_for_request(
        wrapped_component, dummy_request_1.__request_path__, {}, {}
    )

    signature = inspect.signature(dummy_request_1)
    parameter = signature.parameters

    assert path == "/__TEST_PATH__"
    assert (
        request_kwargs["headers"]["dummy_header"]
        == parameter.get("dummy_header").default
    )
    assert (
        request_kwargs["params"]["dummy_query"] == parameter.get("dummy_query").default
    )


def test_missing_argument():
    component = dummy_request_2.__component_parameter__
    wrapped_component = copy.deepcopy(component)

    with pytest.raises(TypeError):
        _, _ = _get_kwarg_for_request(
            wrapped_component, dummy_request_2.__request_path__, {}, {}
        )


def test_private_component():
    assert "private_header" in dummy_request_3.__component_parameter__.header
    assert "private_query" in dummy_request_3.__component_parameter__.query
    assert "private_path" in dummy_request_3.__component_parameter__.path
    assert "private_form" in dummy_request_3.__component_parameter__.form

    assert dummy_request_2.__component_parameter__.body_type == "data"

    assert (
        dummy_request_3.__component_parameter__.header.get("private_header")
        == "__PRIVATE_HEADER__"
    )
    assert (
        dummy_request_3.__component_parameter__.query.get("private_query")
        == "__PRIVATE_QUERY__"
    )
    assert (
        dummy_request_3.__component_parameter__.path.get("private_path")
        == "__PRIVATE_PATH__"
    )
    assert (
        dummy_request_3.__component_parameter__.form.get("private_form")
        == "__PRIVATE_FORM__"
    )
