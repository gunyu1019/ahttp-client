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

.. note:: Only the session-level `before_request`/`after_request` hooks and the request-level `before_hook`/`after_hook` decorators are covered here. See :doc:`retry` for how retries interact with `after_request`, and :doc:`exception` for the `HTTPException` hierarchy raised from a hook.


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

A `GithubService` object is defined by overriding `before_request` and `after_request`.

The token required for authentication is stored as a private attribute and inserted into the header in `before_request`.
When a method on a `GithubService` object is called, such as the `list_repositories` method,
the `before_request` method is called first to insert the necessary HTTP components.

After the HTTP request finishes, the `after_request` method is called to check the HTTP status code.
If the HTTP status code is not 200 (OK), an `HTTPException` (a predefined exception; see :doc:`exception`) is raised.

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

The `repository_topic` method is defined to get the topics of a repository,
and its hooking is defined using the `before_hook` and `after_hook` decorator methods of that same method.

The `before_hook` method inserts the necessary components (authorization key, etc.) before the HTTP request of the `repository_topic` method is called.

The `after_hook` method validates the response before the request function parses the JSON data.

.. warning:: A request-level `after_hook` always runs after any :doc:`retry` attempts have finished; it is not itself retried, even if it raises an exception listed in `retry_on`.
