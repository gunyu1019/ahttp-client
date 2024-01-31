import asyncio
from typing import NamedTuple

import aiohttp

from async_client_decorator import request, Session, Query

loop = asyncio.get_event_loop()


class StationInfo(NamedTuple):
    displayId: str
    id: str
    name: str
    posX: float
    posY: float
    stationId: str
    type: int


@Session.single_session("https://api.yhs.kr")
@request("GET", "/bus/station")
async def station_search_with_query(
    session: Session, response: aiohttp.ClientResponse, name: Query | str
) -> list[StationInfo]:
    data = await response.json()
    return [StationInfo(**x) for x in data]


async def main():
    data = await station_search_with_query(name="bus-station-name")
    print(len(data))


loop.run_until_complete(main())
