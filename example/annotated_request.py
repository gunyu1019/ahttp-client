import asyncio
import aiohttp

from async_client_decorator import request, Session, Query
from typing import Annotated

loop = asyncio.get_event_loop()


class BusAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop)

    @request("GET", "/bus/station")
    async def station_search_with_query(
        self, response: aiohttp.ClientResponse, name: Annotated[str, Query]
    ):
        return await response.json()


async def main():
    async with BusAPI(loop) as client:
        response = await client.station_search_with_query(name="bus-station-name")
        data = await response.json()
        print(len(data))


loop.run_until_complete(main())
