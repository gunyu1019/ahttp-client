=============
API Reference
=============

Component
---------

A component for HTTP sending. (Header, Query, Path, Body) 

.. autoclass:: ahttp_client.component.Component()
    :members:
    :member-order: groupwise

.. autoclass:: ahttp_client.component.Body()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.component.BodyJson()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.component.BodyForm()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.component.Header()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.component.Path()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.component.Query()
    :members:
    :show-inheritance:

Request Core
------------

.. autoclass:: ahttp_client.request.RequestCore()
    :members:
    :member-order: groupwise
    :exclude-members: before_hook, after_hook

    .. py:decorator:: before_hook

        A decorator that registers a coroutine as a pre-invoke hook. 
        A pre-invoke hook is called directly before the HTTP request is called. 
        
        This makes it a useful function to set up authorizations or any type of set up required.

        .. rubric:: Example

        .. code-block:: python

            class GithubService(AsyncSession):
                def __init__(self, token: str):
                    self.token = token
                    super().__init__("https://api.github.com", aiohttp.ClientSession)

                @request("GET", "/users/{user}/repos")
                async def list_repositories(
                    self, response: Response, user: Annotated[str, Path]
                ) -> list[dict[str, Any]]:
                    return response.json()

                @list_repositories.before_hook
                async def authorization(self, req_obj: RequestCore, path: str):
                    req_obj.headers["Authorization"] = f"Bearer: {self.token}"
                    return req_obj, path

    .. py:decorator:: after_hook

        A decorator that registers a coroutine as a post-invoke hook. 
        A post-invoke hook is called directly after the returned HTTP response. 
        
        This makes it a useful function to check correct response or any type of clean up response data.

        .. rubric:: Example

        .. code-block:: python

            class GithubService(AsyncSession):
                def __init__(self):
                    super().__init__("https://api.github.com", aiohttp.ClientSession)

                @request("GET", "/users/{user}/repos")
                async def list_repositories(
                    self, response: Response, user: Annotated[str, Path]
                ) -> list[dict[str, Any]]:
                    return response.json()

                @list_repositories.after_hook
                async def validation_status(self, response: Response):
                    if response.status != 200:
                        raise Exception("ERROR!")
                    return response

.. autodecorator:: ahttp_client.request.request(method: str, path: str)

.. autodecorator:: ahttp_client.request.get(path: str)

.. autodecorator:: ahttp_client.request.post(path: str)

.. autodecorator:: ahttp_client.request.options(path: str)

.. autodecorator:: ahttp_client.request.patch(path: str)

.. autodecorator:: ahttp_client.request.put(path: str)

.. autodecorator:: ahttp_client.request.delete(path: str)

    Same feature as `ahttp_client.request`.


Response
--------

.. autoclass:: ahttp_client.response.Response()
    :members:
    :member-order: groupwise


Session
-------

.. autoclass:: ahttp_client.session.AsyncSession()
    :members:
    :member-order: groupwise
    :exclude-members: single_session

    .. py:decorator:: single_session(base_url: str, session: type, **session_kwargs)

        A single session for one request.
        
        :param str base_url: base url of the API.
        :param type session: HTTP session class used for processing requests.
        :param session_kwargs: Keyword arguments passed to the HTTP session class.
        
        .. rubric:: Example

        The session is defined through the function's decoration.


        .. code-block:: python

            @AsyncSession.single_session("https://api.yhs.kr", aiohttp.ClientSession)
            @request("GET", "/bus/station")
            async def station_query(
                session: AsyncSession, name: Query | str
            ) -> Response:
                pass

.. seealso::
    This page covers the core request/component/session API. The backend
    adapter classes have their own page at :doc:`backend`, retry
    configuration at :doc:`retry`, the serializer/deserializer classes at
    :doc:`serialization`, and the HTTP exception hierarchy at
    :doc:`exception`.
