# aiohttp-client-decorator
A package makes it easy to write aiohttp Client. (WIP)

```python
import asyncio
import aiohttp
from aiohttp_route_decorator import request, Requestable, Header

loop = asyncio.get_event_loop()


class A(Requestable):
    def __init__(self, loop):
        super().__init__("https://base_url", loop)
    
    @request("GET", "/status")
    async def status(
            self,
            response: aiohttp.ClientResponse,
            authorization: Header | str
    ):
        return await response.json() 


async def main():
    session = A(loop)
    data = await session.status(authorization="KEY")
    print(data)


loop.run_until_complete(main())
```