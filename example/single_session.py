import asyncio
import aiohttp

from ahttp_client import AsyncSession, Query, Response, request
from typing import NamedTuple


class StationInfo(NamedTuple):
    arrivalStationId: int
    code: str
    displayName: str
    id: str
    name: str
    posX: float
    posY: float
    subway: str
    subwayId: int


@AsyncSession.single_session("https://api.yhs.kr", aiohttp.ClientSession)
@request("GET", "/metro/station")
async def station_search_with_query(
    session: AsyncSession, response: Response, name: Query | str
) -> list[StationInfo]:
    data = response.json()
    return [StationInfo(**x) for x in data]


async def main():
    data = await station_search_with_query(name="metro-station-name")
    print(len(data))


asyncio.run(main())
