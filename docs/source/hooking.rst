==========================
Pre Hooking / Post Hooking
==========================
In `ahttp_client`, hooking means refining data before and after an HTTP request is received.
A hooking supports session unit hooking and request unit hooking.

A hooking is used as follows.

* Before Hook (Pre-request):
    - Set up the required HTTP component (e.g. authorization).
    - Validate that the correct arguments are given.
* After Hook (Post-request)
    - Parse the raw response data into a data class.
    - Act based on the HTTP status code.

.. note:: This page only covers the session-level `before_request`/`after_request` hooks and the request-level `before_hook`/`after_hook` decorators. For how retries interact with `after_request`, see :doc:`retry`. For the `HTTPException` hierarchy a hook can raise, see :doc:`exception`.


Session Hooking
---------------
A Session unit hooking is created by overridding a method.

.. code-block:: python
    :linenos:
    :caption: Hooking of Session Unit Example

    class GithubService(AsyncSession):
        def __init__(self, token: str):
            self._token = token  # Private Attribute
            super().__init__("https://api.github.com", aiohttp.ClientSession)
        
        # overriding before_request method
        async def before_request(self, req_obj: RequestCore, path: str):
            req_obj.headers["Authorization"] = self._token
            req_obj.headers["Accepts"] = "application/vnd.github+json;"
            return req_obj, path

        # overriding after_request method
        async def after_request(self, response: Response):
            if response.status != 200:
                raise HTTPException()
            return response

        @request("GET", "/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

`GithubService` overrides `before_request` and `after_request` directly.

The token is stored as a private attribute, and `before_request` inserts it into the header. Whenever a method on the object is called, such as `list_repositories`, `before_request` runs first and adds the HTTP components a request needs.

`after_request` runs once the HTTP request finishes and checks the status code. A status other than 200 (OK) raises `HTTPException`, a predefined exception (see :doc:`exception`).

Request Hooking
---------------
A request unit hooking is created using the decorating method.

.. code-block:: python
    :linenos:
    :caption: Hooking of Request Unit Example

    token = "GITHUB TOKEN"

    @AsyncSession.single_session("https://api.github.com", aiohttp.ClientSession)
    @request("GET", "/repos/{user}/{repo}/topics")
    async def repository_topic(
        session: AsyncSession,
        response: Response,
        user: Annotated[str, Path],
        repo: Annotated[str, Path]
    ) -> list[str]:
        return response.json()["names"]

    # before_hook method
    @repository_topic.before_hook
    async def before_hook(session: AsyncSession, req_obj: RequestCore, path: str):
        req_obj.headers["Authorization"] = token
        req_obj.headers["Accepts"] = "application/vnd.github+json;"
        return req_obj, path

    # after_hook method
    @repository_topic.after_hook
    async def after_hook(session: AsyncSession, response: Response):
        if response.status != 200:
            raise HTTPException()
        return response

`repository_topic` fetches the topics of a repository, and its `before_hook`/`after_hook` decorators define the hooking right on that same method.

`before_hook` inserts what the request needs (an authorization key, for example) before `repository_topic` makes the HTTP call.

`after_hook` validates the response before the request function parses the JSON.

.. warning:: A request-level `after_hook` always runs after any :doc:`retry` attempts have finished. It is not retried itself, even if it raises an exception listed in `retry_on`.
