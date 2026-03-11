import asyncio
import aiohttp

from ahttp_client import request, Session, Query
from typing import Annotated


class MetroAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop=loop)

    @request("GET", "/metro/station")
    async def station_search_with_query(self, response: aiohttp.ClientResponse, name: Annotated[str, Query]):
        return await response.json()


async def main():
    async with MetroAPI() as client:
        data = await client.station_search_with_query(name="metro-station-name")
        print(len(data))


asyncio.run(main())
