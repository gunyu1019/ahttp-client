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

Deserialize an HTTP response directly into Pydantic models.
"""

import asyncio
from typing import Annotated

import aiohttp
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ahttp_client import AsyncSession, Query, get
from ahttp_client.serializer import deserialize


class Station(BaseModel):
    arrival_station_id: int
    code: str
    display_name: str
    id: str
    name: str
    pos_x: float
    pos_y: float
    subway: str
    subway_id: int

    model_config = ConfigDict(alias_generator=to_camel)


class MetroAPI(AsyncSession):
    def __init__(self) -> None:
        super().__init__("https://api.yhs.kr", aiohttp.ClientSession)

    @get("/metro/station", directly_response=True)
    @deserialize(by_alias=True)
    async def search_stations(
        self,
        name: Annotated[str, Query],
    ) -> list[Station]:
        raise AssertionError("direct deserialization skips the method body")


async def main() -> None:
    async with MetroAPI() as client:
        stations = await client.search_stations(name="강남")
        for station in stations:
            print(station.name)


if __name__ == "__main__":
    asyncio.run(main())
