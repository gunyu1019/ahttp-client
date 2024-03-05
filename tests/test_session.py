import pytest

from ahttp_client import *
from ahttp_client.request import RequestCore


@pytest.fixture
def test_method_for_single_session():
    @Session.single_session("https://test_base_url")
    @request("GET", "/")
    async def test_request(session: Session) -> None:
        pass

    return test_request


def test_single_session(test_method_for_single_session):
    assert hasattr(test_method_for_single_session, "__core__")
    assert isinstance(test_method_for_single_session.__core__, RequestCore)

    assert test_method_for_single_session.before_hook == test_method_for_single_session.__core__.before_hook
    assert test_method_for_single_session.after_hook == test_method_for_single_session.__core__.after_hook
