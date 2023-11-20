# async-client-decorator

Using `@decorator` to esaily request an HTTP Client<br/>

## Example

```python
import asyncio
import aiohttp
from async_client_decorator import request, Requestable, Header

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