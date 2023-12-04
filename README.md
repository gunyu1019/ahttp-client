 # async-client-decorator

Using `@decorator` to esaily request an HTTP Client<br/>
This framework based on [aiohttp](https://github.com/aio-libs/aiohttp)'s http client framework.<br/>

Use Union Type to describe the elements required in an HTTP request.


## Installation
**Python 3.10 or higher is required.**

```pip
pip install async_client_decorator
```

## Quick Example

An example is the API provided by the [BUS API](https://github.com/gunyu1019/trafficAPI).
```python
import asyncio
import aiohttp
from async_client_decorator import request, Session, Query

loop = asyncio.get_event_loop()


class BusAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop)

    @request("GET", "/bus/station")
    async def station_search_with_query(
                self,
                response: aiohttp.ClientResponse,
                name: Query | str
    ):
        return await response.json() 


async def main():
    async with BusAPI(loop) as client:
        response = await client.station_search_with_query(name="bus-station-name")
        data = await response.json()
        print(len)

loop.run_until_complete(main())
```