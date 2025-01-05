=========
Extension
=========
A Extension page describes features that are outside the scope of ahttp_client's native functionality but may be helpful for development.

Mulitple Hooking
----------------

A decorator method that hook mulitple methods in a HTTP request.
In normal condition, an HTTP request can only have one hooking: before the request, and after the request.

.. decorator:: multiple_hook(hook, index)

    Use this method, if more than one pre-invoke hooks or post-invoke hooks need.

    :param  hook: Contains the decorator function used for hooking. 
        This can be `RequestCore.before_hook()` or `RequestCore.after_hook()`.
    
    :param Optional[int] index: Order of invocation in invoke-hook

    .. rubric:: Example

    .. code-block:: python
        :linenos:
    
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

            @multiple_hook(station_search_with_query.before_hook)
            async def before_hook_1(self, obj, path):
                # Set-up before request
                return obj, path

            @multiple_hook(station_search_with_query.before_hook)
            async def before_hook_2(self, obj, path):
                # Set-up before request
                return obj, path

Pydantic Response Model
-----------------------

.. note:: `pydantic` pacakage is required.

    .. code-block:: bash

        pip install pydantic

Returns ths json formatted data from HTTP request, 
serialized and returned as a class extended with `pydantic.BaseModel`.

.. autodecorator:: ahttp_client.extension.pydantic_response_model(model)