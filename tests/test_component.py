import aiohttp
import pytest

from typing import Any
from ahttp_client import *


@pytest.fixture
def test_method_form_data_type_1():
    @request("GET", "/test_path")
    async def test_request(
        session: Session,
        test_body: str | Form = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_form_data_type_2():
    @request("GET", "/test_path")
    async def test_request(
        session: Session,
        test_body: aiohttp.FormData | Body = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_json_data():
    @request("GET", "/test_path")
    async def test_request(
        session: Session,
        test_body: list[Any] | Body = None,
    ) -> None:
        pass

    return test_request


def test_duplicated_body_type():
    with pytest.raises(TypeError) as error_message:

        @request("GET", "/test_path")
        async def test_request(
            session: Session,
            test_body_1: Form | Body = None,
            test_body_2: list[Any] | Body = None,
        ) -> None:
            pass

    assert str(error_message.value) == "Duplicated Form Parameter or Body Parameter."


def test_not_duplicated_body_type():
    @request("GET", "/test_path")
    async def test_request(
        session: Session,
        test_body_1: int | BodyJson = None,
        test_body_2: list[Any] | BodyJson = None,
    ) -> None:
        pass

    assert len(test_request.body_json_parameter) == 2


def test_duplicated_body():
    sample_body = aiohttp.FormData()
    with pytest.raises(TypeError) as error_message:

        @request("GET", "/test_path", body=sample_body)
        async def test_request(
            session: Session,
            test_body: aiohttp.FormData | Body = None,
        ) -> None:
            pass

    assert str(error_message.value) == "Only one Body Parameter or Body is allowed."


def test_form_data_type_1(test_method_form_data_type_1):
    assert test_method_form_data_type_1.is_formal_form is True
    assert test_method_form_data_type_1.is_body is True
    assert test_method_form_data_type_1.body_parameter_type == "data"


def test_form_data_type_2(test_method_form_data_type_2):
    assert test_method_form_data_type_2.is_formal_form is False
    assert test_method_form_data_type_2.is_body is True
    assert test_method_form_data_type_2.body_parameter_type == "data"


def test_json_data(test_method_json_data):
    assert test_method_json_data.is_formal_form is False
    assert test_method_json_data.is_body is True
    assert test_method_json_data.body_parameter_type == "json"
