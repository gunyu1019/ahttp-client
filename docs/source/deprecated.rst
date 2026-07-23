==========
Deprecated
==========
This page archives features that were documented for `ahttp_client` v1 but have since been removed from the package.
It exists so that developers upgrading from v1 can find out what happened to a feature they used to rely on; none of the code below is importable from the current package.

Multiple Hooking
-----------------
.. deprecated:: 2.0
    Removed. There is no direct replacement.

`multiple_hook` used to let more than one function hook the same before/after stage of a request:

.. code-block:: python
    :linenos:

    class MetroAPI(AsyncSession):
        def __init__(self):
            super().__init__("https://api.yhs.kr", aiohttp.ClientSession)

        @request("GET", "/metro/station")
        async def station_search_with_query(
                self,
                response: Response,
                name: Query | str
        ) -> dict[str, Any]:
            return response.json()

        @multiple_hook(station_search_with_query.before_hook)
        async def before_hook_1(self, obj, path):
            # Set-up before request
            return obj, path

        @multiple_hook(station_search_with_query.before_hook)
        async def before_hook_2(self, obj, path):
            # Set-up before request
            return obj, path

As of v2.0, `RequestCore.before_hook`/`after_hook` (see :doc:`hooking`) each accept only a single function.
If more than one action is needed at a stage, combine them inside one hook function instead of stacking `multiple_hook` calls.

Pydantic Response Model
-------------------------
.. deprecated:: 2.0
    Removed. Replaced by :doc:`serialization`.

`ahttp_client.extension.pydantic_response_model(model)` used to deserialize a JSON response into a `pydantic.BaseModel` subclass by passing the model type directly: `@pydantic_response_model(Repository)`.

Its role is now filled by `@deserialize` from :doc:`serialization`, which additionally supports `dataclasses` and `marshmallow` models and can also be paired with `@serialize` for the request body:

.. code-block:: python

    from ahttp_client.serializer import deserialize

    @get("/users/{user}/repos", directly_response=True)
    @deserialize()
    async def list_repositories(self, response: Response, user: Annotated[str, Path]) -> list[Repository]:
        raise AssertionError("direct deserialization skips the method body")
