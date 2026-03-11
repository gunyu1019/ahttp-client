import asyncio
import aiohttp
import pydantic

from ahttp_client import request, Session, Query, Body
from ahttp_client.extension import pydantic_response_model
from pydantic.alias_generators import to_camel
from typing import Annotated


class PydanticModel(pydantic.BaseModel):
    arrival_station_id: int
    code: str
    display_name: str
    id: str
    name: str
    pos_x: float
    pos_y: float
    subway: str
    subway_id: int

    model_config = pydantic.ConfigDict(alias_generator=to_camel)


class MetroAPI(Session):
    def __init__(self):
        super().__init__("https://api.yhs.kr")

    @pydantic_response_model()
    @request("GET", "/metro/station", directly_response=True)
    async def station_search_with_query(
        self, response: aiohttp.ClientResponse, name: Annotated[str, Query]
    ) -> PydanticModel:
        pass


async def main():
    async with MetroAPI() as client:
        data = await client.station_search_with_query(name="강남")
        print(data)


asyncio.run(main())
