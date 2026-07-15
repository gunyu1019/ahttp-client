import asyncio
import aiohttp

from ahttp_client import AsyncSession, Query, Response, request
from typing import Annotated


class MetroAPI(AsyncSession):
    def __init__(self):
        super().__init__("https://api.yhs.kr", aiohttp.ClientSession)

    @request("GET", "/metro/station")
    async def station_search_with_query(
        self, response: Response, name: Annotated[str, Query]
    ):
        return response.text()


async def main():
    async with MetroAPI() as client:
        data = await client.station_search_with_query(name="metro-station-name")
        print(len(data))


asyncio.run(main())
