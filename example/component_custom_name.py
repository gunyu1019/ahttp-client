import asyncio
import aiohttp

from ahttp_client import request, Session, Query
from typing import Any, Annotated

loop = asyncio.get_event_loop()


class MetroAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop=loop)

    @request("GET", "/metro/station", directly_response=True)
    async def station_search_with_query(
        self,
        response: aiohttp.ClientResponse,
        station_name: Annotated[str, Query.custom_name("name")],
    ) -> aiohttp.ClientResponse:
        pass


async def main():
    async with MetroAPI(loop) as client:
        response = await client.station_search_with_query(station_name="강남")
        data = await response.json()
        print(data)


loop.run_until_complete(main())
