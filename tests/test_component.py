import pytest

from async_client_decorator import *
from async_client_decorator.component import Component


def test_duplicated_body_type():
    sample_component = Component()
    with pytest.raises(ValueError) as error_message:
        sample_component.add_form("DUMMY_KEY", "DUMMY_VALUE")
        sample_component.set_body({"DUMMY_KEY": "DUMMY_VALUE"})
    assert str(error_message.value) == "Use only one Form Parameter or Body Parameter."


def test_incorrect_body_type():
    sample_component = Component()
    with pytest.raises(TypeError) as error_message:
        sample_component.set_body(1)
    assert (
        str(error_message.value)
        == "Body parameter can only have aiohttp.FormData or dict, list."
    )


def test_duplicated_body():
    sample_component = Component()
    with pytest.raises(ValueError) as error_message:
        sample_component.set_body({"DUMMY_KEY": "DUMMY_VALUE"})
        sample_component.set_body({"DUMMY_KEY": "DUMMY_VALUE"})
    assert str(error_message.value) == "Only one Body Parameter is allowed."


def test_form_data():
    sample_component = Component()
    sample_component.add_form("DUMMY_KEY", "DUMMY_VALUE")

    assert sample_component.is_formal_form() is True
    assert sample_component.is_body() is True
    assert sample_component.body_type == "data"


def test_json_data():
    sample_component = Component()
    sample_component.set_body({"DUMMY_KEY": "DUMMY_VALUE"})

    assert sample_component.is_formal_form() is False
    assert sample_component.is_body() is True
    assert sample_component.body_type == "json"
