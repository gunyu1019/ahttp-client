import asyncio
import aiohttp

from ahttp_client import AsyncSession, Query, Response, request
from typing import Annotated


class MetroAPI(AsyncSession):
    def __init__(self):
        super().__init__("https://api.yhs.kr", aiohttp.ClientSession)

    @request("GET", "/metro/station", directly_response=True)
    async def station_search_with_query(  # type: ignore[empty-body]
        self,
        response: Response,
        station_name: Annotated[str, Query.custom_name("name")],
    ) -> Response:
        pass


async def main():
    async with MetroAPI() as client:
        response = await client.station_search_with_query(station_name="강남")
        data = response.json()
        print(data)


asyncio.run(main())
