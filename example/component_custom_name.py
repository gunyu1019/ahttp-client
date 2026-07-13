import asyncio
import aiohttp

from ahttp_client import request, BaseSession, Query
from typing import Any, Annotated


class MetroAPI(BaseSession):
    def __init__(self):
        super().__init__("https://api.yhs.kr")

    @request("GET", "/metro/station", directly_response=True)
    async def station_search_with_query(  # type: ignore[empty-body]
        self,
        response: aiohttp.ClientResponse,
        station_name: Annotated[str, Query.custom_name("name")],
    ) -> aiohttp.ClientResponse:
        pass


async def main():
    async with MetroAPI() as client:
        response = await client.station_search_with_query(station_name="강남")
        data = await response.json()
        print(data)


asyncio.run(main())
