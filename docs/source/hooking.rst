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

    class GithubService(Session):
        def __init__(self, token: str):
            self._token = token  # Private Attribute
            super().__init__("https://api.github.com")
        
        # overridding before_hook method
        async def before_hook(self, req_obj: RequestCore, path: str):
            req_obj.headers["Authorization"] = self._token
            req_obj.headers["Accepts"] = "application/vnd.github+json;"
            return req_obj, path

        # overridding after_hook method
        async def after_hook(self, response: aiohttp.ClientResponse):
            if response.status_code != 200:
                raise HTTPException()
            return response

        @request("GET", "/users/{user}/repos")
        def list_repositories(
            self, user: Annotated[str, Path]
        ) -> dict[str, Any]:
            return await response.json()

A `Github Service` object are defined by overriding before_hook and after_hook.

Store the token required for authentication as a private attribute and insert it in header in before_hook.
When a method on a `GithubService` object is called, such as `list_repositories` method, 
`before_hook` method is called first to insert the necessary HTTP compoenents.

After finishing the HTTP request, the `after_hook` method is called to check HTTP status code.
If the HTTP status code is not 200(OK), a HTTPException(A predefined exception) is raised.

Request Hooking
---------------
A request unit hooking is created using the decorating method.

.. code-block:: python
    :linenos:
    :caption: Hooking of Request Unit Example

    token = "GITHUB TOKEN"

    @Session.single_session(base_url="https://api.github.com")
    @request("GET", "/repos/{user}/{repo}/topics", directly_response=True)
    def repository_topic(
        self, 
        user: Annotated[str, Path],
        repo: Annotated[str, Path]
    ) -> list[str]:
        pass

    # before_hook method
    @repository_topic.before_hook
    async def before_hook(self, req_obj: RequestCore, path: str):
        req_obj.headers["Authorization"] = token
        req_obj.headers["Accepts"] = "application/vnd.github+json;"
        return req_obj, path

    # after_hook method
    @repository_topic.after_hook
    async def after_hook(self, response: aiohttp.ClientResponse):
        data = await response.json()
        return data["names"]

To get the topic of a repository, `repository_topic` method defined.
And defined the hooking with the before_hook decoration method and after_hook decoration method of the `repository_topic` method.

The before_hook method inserts the necessary compoenents(authorization key...etc) before the HTTP request of the repository_topic method is called.

The after_hook method refines and return the result received in response.
It removes unnesscessary keys.