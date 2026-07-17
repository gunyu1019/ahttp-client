"""Deserialize an HTTP response directly into Pydantic models."""

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
