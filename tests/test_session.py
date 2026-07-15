import pytest

import aiohttp

from ahttp_client import AsyncSession, BaseSession, request
from ahttp_client.request import RequestCore


@pytest.fixture
def test_method_for_single_session():
    @AsyncSession.single_session("https://test_base_url", aiohttp.ClientSession)
    @request("GET", "/")
    async def test_request(session: BaseSession) -> None:
        pass

    return test_request


def test_single_session(test_method_for_single_session):
    assert hasattr(test_method_for_single_session, "__core__")
    assert isinstance(test_method_for_single_session.__core__, RequestCore)

    assert (
        test_method_for_single_session.before_hook
        == test_method_for_single_session.__core__.before_hook
    )
    assert (
        test_method_for_single_session.after_hook
        == test_method_for_single_session.__core__.after_hook
    )
