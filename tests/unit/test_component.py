import io
from typing import Annotated, Any

import pytest

from ahttp_client import (
    BaseSession,
    Body,
    BodyForm,
    BodyFormEncoding,
    BodyJson,
    BodyType,
    request,
)


@pytest.fixture
def test_method_form_data_type_1():
    @request("GET", "/test_path")
    async def test_request(
        session: BaseSession,
        test_body: str | BodyForm = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_form_data_type_2():
    @request("GET", "/test_path")
    async def test_request(
        session: BaseSession,
        test_body: io.BytesIO | Body = None,
    ) -> None:
        pass

    return test_request


@pytest.fixture
def test_method_json_data():
    @request("GET", "/test_path")
    async def test_request(
        session: BaseSession,
        test_body: list[Any] | Body = None,
    ) -> None:
        pass

    return test_request


def test_duplicated_body_type():
    with pytest.raises(TypeError) as error_message:

        @request("GET", "/test_path")
        async def test_request(
            session: BaseSession,
            test_body_1: BodyForm | Body = None,
            test_body_2: list[Any] | Body = None,
        ) -> None:
            pass

    assert str(error_message.value) == (
        "Duplicated Body Form Parameter, Body Json Parameter or Body Parameter."
    )


def test_not_duplicated_body_type():
    @request("GET", "/test_path")
    async def test_request(
        session: BaseSession,
        test_body_1: int | BodyJson = None,
        test_body_2: list[Any] | BodyJson = None,
    ) -> None:
        pass

    assert len(test_request.body_json_parameter) == 2


def test_duplicated_body():
    sample_body = io.BytesIO()
    with pytest.raises(TypeError) as error_message:

        @request("GET", "/test_path", body=sample_body)
        async def test_request(
            session: BaseSession,
            test_body: io.BytesIO | Body = None,
        ) -> None:
            pass

    assert str(error_message.value) == "Only one Body Parameter or Body is allowed."


def test_form_data_type_1(test_method_form_data_type_1):
    assert test_method_form_data_type_1.is_formal_form is True
    assert test_method_form_data_type_1.is_body is True
    assert test_method_form_data_type_1.body_parameter_type == BodyType.URL_ENCODED


def test_form_data_type_2(test_method_form_data_type_2):
    assert test_method_form_data_type_2.is_formal_form is False
    assert test_method_form_data_type_2.is_body is True
    assert test_method_form_data_type_2.body_parameter_type == BodyType.RAW


def test_json_data(test_method_json_data):
    assert test_method_json_data.is_formal_form is False
    assert test_method_json_data.is_body is True
    assert test_method_json_data.body_parameter_type == BodyType.JSON


def _filled_component_request(request_core, *values):
    bound_arguments = request_core._signature.bind(None, *values)
    bound_arguments.apply_defaults()
    filled_request = request_core.copy()
    filled_request._fill_parameter(None, bound_arguments)
    return filled_request


def test_body_json_builds_nested_and_renamed_payload():
    @request("POST", "/items")
    async def create_item(
        _: BaseSession,
        name: Annotated[str, BodyJson.custom_key("item.name")],
        quantity: Annotated[int, BodyJson.custom_key("item.quantity")],
        send_email: Annotated[bool, BodyJson.custom_name("sendEmail")],
    ) -> None:
        pass

    filled_request = _filled_component_request(create_item, "notebook", 2, True)

    assert create_item.body_type == BodyType.JSON
    assert set(create_item.body_json_parameter) == {"name", "quantity", "sendEmail"}
    assert filled_request.body == {
        "item": {"name": "notebook", "quantity": 2},
        "sendEmail": True,
    }


def test_body_form_defaults_to_url_encoded_without_file_fields():
    @request("POST", "/tokens")
    async def create_token(
        _: BaseSession,
        client_id: Annotated[str, BodyForm.to_camel()],
        scope: BodyForm,
    ) -> None:
        pass

    filled_request = _filled_component_request(create_token, "client-1", "read write")

    assert create_token.body_type == BodyType.URL_ENCODED
    assert filled_request.body == {"clientId": "client-1", "scope": "read write"}
    assert filled_request._body_file is None


def test_body_form_file_field_selects_multipart_and_preserves_metadata():
    @request("POST", "/uploads")
    async def upload(
        _: BaseSession,
        description: BodyForm,
        document: Annotated[bytes, BodyForm.metadata("report.txt", "text/plain")],
    ) -> None:
        pass

    filled_request = _filled_component_request(
        upload, "quarterly report", b"file content"
    )

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body == {"description": "quarterly report"}
    assert filled_request._body_file == {
        "document": ("report.txt", b"file content", "text/plain"),
    }


def test_file_like_body_form_field_uses_multipart_automatically():
    @request("POST", "/uploads")
    async def upload(_: BaseSession, document: Annotated[io.BytesIO, BodyForm]) -> None:
        pass

    document = io.BytesIO(b"file content")
    filled_request = _filled_component_request(upload, document)

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body is None
    assert filled_request._body_file == {"document": ("document", document, None)}


def test_form_encoding_can_force_multipart_without_file_fields():
    @request("POST", "/uploads", form_encoding=BodyFormEncoding.FORM_DATA)
    async def upload(_: BaseSession, description: BodyForm) -> None:
        pass

    filled_request = _filled_component_request(upload, "quarterly report")

    assert upload.body_type == BodyType.FORM_DATA
    assert filled_request.body == {"description": "quarterly report"}
    assert filled_request._body_file is None
