import asyncio
import aiohttp
import pydantic
import pydantic.alias_generators

from async_client_decorator import request, Session, Query
from async_client_decorator.extension import get_pydantic_response_model
from typing import Annotated

loop = asyncio.get_event_loop()


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

    model_config = pydantic.ConfigDict(alias_generator=pydantic.alias_generators.to_camel)


class MetroAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop=loop)

    @get_pydantic_response_model()
    @request("GET", "/metro/station", directly_response=True)
    async def station_search_with_query(
        self, response: aiohttp.ClientResponse, name: Annotated[str, Query()]
    ) -> PydanticModel:
        pass


async def main():
    async with MetroAPI(loop) as client:
        data = await client.station_search_with_query(name="강남")
        print(data)


loop.run_until_complete(main())
