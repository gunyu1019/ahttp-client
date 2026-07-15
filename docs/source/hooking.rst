==========================
Pre Hooking / Post Hooking
==========================
In `ahttp_client`, hooking means refining data before and after receiving a HTTP request.
A hooking supports session unit hooking and request unit hooking.

A hooking is used as follows.

* Before Hook (Pre-request):
    - Setup the required HTTP-Compoenent (ex. authorization)
    - Vaildate that the correct arguments are in.
* After Hook (Post-request)
    - Parses data in raw form to a data class.
    - Act based on HTTP status code


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
        
        # overridding before_request method
        async def before_request(self, req_obj: RequestCore, path: str):
            req_obj.headers["Authorization"] = self._token
            req_obj.headers["Accepts"] = "application/vnd.github+json;"
            return req_obj, path

        # overridding after_request method
        async def after_request(self, response: Response):
            if response.status != 200:
                raise HTTPException()
            return response

        @request("GET", "/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

A `Github Service` object is defined by overriding before_request and after_request.

Store the token required for authentication as a private attribute and insert it in header in before_request.
When a method on a `GithubService` object is called, such as `list_repositories` method, 
`before_request` method is called first to insert the necessary HTTP compoenents.

After finishing the HTTP request, the `after_request` method is called to check HTTP status code.
If the HTTP status code is not 200(OK), a HTTPException(A predefined exception) is raised.

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

To get the topic of a repository, `repository_topic` method defined.
And defined the hooking with the before_hook decoration method and after_hook decoration method of the `repository_topic` method.

The before_hook method inserts the necessary compoenents(authorization key...etc) before the HTTP request of the repository_topic method is called.

The after_hook method validates the response before the request function parses the JSON data.
