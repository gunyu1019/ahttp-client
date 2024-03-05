import asyncio
from typing import NamedTuple

import aiohttp

from ahttp_client import request, Session, Query

loop = asyncio.get_event_loop()


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


@Session.single_session("https://api.yhs.kr")
@request("GET", "/metro/station")
async def station_search_with_query(
    session: Session, response: aiohttp.ClientResponse, name: Query | str
) -> list[StationInfo]:
    data = await response.json()
    return [StationInfo(**x) for x in data]


async def main():
    data = await station_search_with_query(name="metro-station-name")
    print(len(data))


loop.run_until_complete(main())
