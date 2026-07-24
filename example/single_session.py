"""MIT License

Copyright (c) 2023-present gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
async def station_search_with_query(session: AsyncSession, response: Response, name: Query | str) -> list[StationInfo]:
    data = response.json()
    return [StationInfo(**x) for x in data]


async def main():
    data = await station_search_with_query(name="metro-station-name")
    print(len(data))


asyncio.run(main())
