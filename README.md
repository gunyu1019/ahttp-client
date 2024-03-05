 # ahttp-client
 
![PyPI - Version](https://img.shields.io/pypi/v/ahttp-client?style=flat)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ahttp-client?style=flat)
![PyPI - License](https://img.shields.io/pypi/l/ahttp-client?style=flat)

Using `@decorator` to easily request an HTTP Client<br/>
This framework based on [aiohttp](https://github.com/aio-libs/aiohttp)'s http client framework.<br/>

Use Union Type to describe the elements required in an HTTP request.


## Installation
**Python 3.10 or higher is required.**

```pip
pip install ahttp-client
```

## Quick Example

An example is the API provided by the [BUS API](https://github.com/gunyu1019/trafficAPI).

```python
import asyncio
import aiohttp
from ahttp_client import request, Session, Query
from typing import Any

loop = asyncio.get_event_loop()


class MetroAPI(Session):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__("https://api.yhs.kr", loop=loop)

    @request("GET", "/metro/station")
    async def station_search_with_query(
            self,
            response: aiohttp.ClientResponse,
            name: Query | str
    ) -> dict[str, Any]:
        return await response.json()


async def main():
    async with MetroAPI(loop) as client:
        data = await client.station_search_with_query(name="metro-station-name")
        print(len(data))


loop.run_until_complete(main())
```
