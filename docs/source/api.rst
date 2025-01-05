=============
API Reference
=============

Component
---------

A component for HTTP sending. (Header, Query, Path, Body) 

.. autoclass:: ahttp_client.component.Component()
    :members:
    :member-order: groupwise

.. autoclass:: ahttp_client.body_json.BodyJson()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.body.Body()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.form.Form()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.header.Header()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.path.Path()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.query.Query()
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

            class GithubService(Session):
                def __init__(self, token: str):
                    self.token = token
                    super().__init__("https://api.github.com")

                @request("GET", "/users/{user}/repos")
                def list_repositories(user: Annotated[str, Path]) -> dict[str, Any]:
                    pass

                @list_repoisitories.before_hook
                async def authorization(self, req_obj: RequestCore, path: str):
                    req_obj.header["Authorization"] = f"Bearer: {self.token}"
                    return req_obj, path

    .. py:decorator:: after_hook

        A decorator that registers a coroutine as a post-invoke hook. 
        A post-invoke hook is called directly after the returned HTTP response. 
        
        This makes it a useful function to check correct response or any type of clean up response data.

        .. rubric:: Example

        .. code-block:: python

            class GithubService(Session):
                def __init__(self):
                    super().__init__("https://api.github.com")

                @request("GET", "/users/{user}/repos")
                def list_repositories(user: Annotated[str, Path]) -> dict[str, Any]:
                    pass

                @list_repoisitories.after_hook
                async def validation_status(self, response: aiohttp.ClientResponse):
                    if response.status_code != 200:
                        raise Exception("ERROR!")
                    return await response.json()

.. autodecorator:: ahttp_client.request.request(method: str, path: str)

.. autodecorator:: ahttp_client.request.get(path: str)

.. autodecorator:: ahttp_client.request.post(path: str)

.. autodecorator:: ahttp_client.request.options(path: str)

.. autodecorator:: ahttp_client.request.put(path: str)

.. autodecorator:: ahttp_client.request.delete(path: str)

    Same feature as `ahttp_client.request`.


Session
-------

.. autoclass:: ahttp_client.session.Session()
    :members:
    :member-order: groupwise
    :exclude-members: single_session

    .. py:decorator:: single_session(base_url: str, loop: Optional[asyncio.AbstractEventLoop], **session_kwargs)

        A single session for one request.
        
        :param str base_url: base url of the API.
        :param asynico.AbstractEventLoop loop: event loop used for processing HTTP requests.
        :param  session_kwargs: Keyword argument used in `aiohttp.ClientSession`
        
        .. rubric:: Example

        The session is defined through the function's decoration.


        .. code-block:: python

            @Session.single_session("https://api.yhs.kr")
            @request("GET", "/bus/station")
            async def station_query(session: Session, name: Query | str) -> aiohttp.ClientResponse:
                pass