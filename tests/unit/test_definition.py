import io
import pytest

from typing import Annotated, Any

from ahttp_client import (
    BaseSession,
    Body,
    BodyForm,
    BodyType,
    Header,
    Path,
    Query,
    Response,
    request,
)


@pytest.fixture
def test_method_with_parameter():
    @request("GET", "/{test_path}")
    async def test_request(
        session: BaseSession,
        test_response: Response,
        test_path: str | Path = "__TEST_PATH__",
        test_query: str | Query = "__TEST_PARAMETER__",
        test_header: str | Header = "__TEST_HEADER__",
        test_body: dict | Body = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_with_annotated():
    @request("GET", "/{test_path}")
    async def test_request(
        session: BaseSession,
        test_path: Annotated[str, Path],
        test_query: Annotated[str, Query],
        test_header: Annotated[str, Header],
        test_body: Annotated[dict, Body],
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_with_decorator_parameter():
    @request(
        "GET",
        "/{test_path}",
        path_parameter=["test_path"],
        query_parameter=["test_query"],
        header_parameter=["test_header"],
        body_parameter="test_body",
    )
    async def test_request(
        session: BaseSession,
        test_path: str,
        test_query: str,
        test_header: str,
        test_body: io.BytesIO = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_component_custom_name():
    @request("GET", "/test_path")
    async def test_request(
        _: BaseSession,
        test_header: Annotated[str, Header.custom_name("custom_header_name")],
        test_query: Annotated[int, Query.to_pascal()],
        test_form: Annotated[str, BodyForm.to_camel()],
    ) -> None:
        pass

    return test_request


def test_component_parameter_1(test_method_with_parameter):
    request_core = test_method_with_parameter
    assert "test_header" in request_core.header_parameter
    assert "test_query" in request_core.query_parameter
    assert "test_path" in request_core.path_parameter
    assert "test_response" in request_core.response_parameter

    assert request_core.body_parameter.name == "test_body"
    assert request_core.body_parameter_type == BodyType.JSON


def test_component_parameter_2(test_method_with_decorator_parameter):
    request_core = test_method_with_decorator_parameter
    assert "test_header" in request_core.header_parameter
    assert "test_query" in request_core.query_parameter
    assert "test_path" in request_core.path_parameter

    assert request_core.body_parameter.name == "test_body"
    assert request_core.body_parameter_type == BodyType.RAW


def test_component_parameter_3(test_method_with_annotated):
    request_core = test_method_with_annotated
    assert "test_header" in request_core.header_parameter
    assert "test_query" in request_core.query_parameter
    assert "test_path" in request_core.path_parameter

    assert request_core.body_parameter.name == "test_body"
    assert request_core.body_parameter_type == BodyType.JSON


def test_component_custom_name(test_method_component_custom_name):
    assert "custom_header_name" in test_method_component_custom_name.header_parameter
    assert "TestQuery" in test_method_component_custom_name.query_parameter
    assert "testForm" in test_method_component_custom_name.body_form_parameter

    assert "test_header" not in test_method_component_custom_name.header_parameter
    assert "test_query" not in test_method_component_custom_name.query_parameter
    assert "test_form" not in test_method_component_custom_name.body_form_parameter

    assert (
        test_method_component_custom_name.header_parameter["custom_header_name"].name
        == "test_header"
    )
    assert (
        test_method_component_custom_name.query_parameter["TestQuery"].name
        == "test_query"
    )
    assert (
        test_method_component_custom_name.body_form_parameter["testForm"].parameter.name
        == "test_form"
    )


def test_body_unsupported_custom_name():
    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/test_path")
        async def test_request(
            _: BaseSession,
            test_body: str | Body.to_pascal(),
        ) -> None:
            pass

    assert str(error_message.value) == "Body.to_pascal is not supported."

    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/test_path")
        async def test_request(
            _: BaseSession,
            test_body: str | Body.to_camel(),
        ) -> None:
            pass

    assert str(error_message.value) == "Body.to_camel is not supported."

    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/test_path")
        async def test_request(
            _: BaseSession,
            test_body: str | Body.custom_name("another_name"),
        ) -> None:
            pass

    assert str(error_message.value) == "Body.custom_name is not supported."


def test_path_unsupported_custom_name():
    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/{TestPath}")
        async def test_request(
            _: BaseSession,
            test_path: str | Path.to_pascal(),
        ) -> None:
            pass

    assert str(error_message.value) == "Path.to_pascal is not supported."

    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/{testPath}")
        async def test_request(
            _: BaseSession,
            test_path: str | Path.to_camel(),
        ) -> None:
            pass

    assert str(error_message.value) == "Path.to_camel is not supported."

    with pytest.raises(NotImplementedError) as error_message:

        @request("GET", "/{test_path}")
        async def test_request(
            _: BaseSession,
            test_path: str | Path.custom_name("another_name"),
        ) -> None:
            pass

    assert str(error_message.value) == "Path.custom_name is not supported."
