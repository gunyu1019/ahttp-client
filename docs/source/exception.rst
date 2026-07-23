=========
Exception
=========
`ahttp_client` provides a ready-made exception class for every standard HTTP 4xx/5xx status code, so error handling does not require manually checking `response.status` and raising a custom exception.

.. code-block:: python
    :linenos:
    :caption: Raising an HTTPException from a Response

    import aiohttp

    from ahttp_client import AsyncSession, HTTPNotFound, Response


    class GithubService(AsyncSession):
        async def after_request(self, response: Response) -> Response:
            response.raise_for_status()
            return response

    async with GithubService("https://api.github.com", aiohttp.ClientSession) as service:
        try:
            await service.list_repositories(user="does-not-exist")
        except HTTPNotFound as exc:
            print(exc.status, exc.url)

`Response.raise_for_status()` looks up the exception class registered for the response's status code and, if one is found, raises it with the response attached. A successful or redirect response (2xx/3xx) is left untouched.

Exception Hierarchy
--------------------
Every exception inherits from :class:`HTTPException <ahttp_client.exception.HTTPException>`, which carries the triggering `response`, its `status` code, and its `url`.

* **HTTPClientError** - base class for 4xx responses. Used directly for a 4xx status code that has no dedicated class below.
* **HTTPServerError** - base class for 5xx responses. Used directly for a 5xx status code that has no dedicated class below.
* One concrete subclass per standard status code, such as `HTTPBadRequest` (400), `HTTPNotFound` (404), `HTTPTooManyRequests` (429), `HTTPInternalServerError` (500), and `HTTPServiceUnavailable` (503).

.. note:: RFC 9110 renamed a few statuses; both the current and legacy names are exported as aliases of the same class: `HTTPPayloadTooLarge`/`HTTPContentTooLarge` (413), `HTTPRequestURITooLong`/`HTTPURITooLong` (414), and `HTTPUnprocessableEntity`/`HTTPUnprocessableContent` (422).

Catching by category, rather than by exact status code, is useful when a request should be retried or logged the same way for any 4xx or any 5xx response:

.. code-block:: python

    from ahttp_client import HTTPClientError, HTTPServerError

    try:
        await service.list_repositories(user="gunyu1019")
    except HTTPClientError:
        ...  # any 4xx status
    except HTTPServerError:
        ...  # any 5xx status

Combining with Retry
----------------------
Because `raise_for_status()` turns a failing response into a typed exception, that exception can be listed directly in `retry_on` (see :doc:`retry`) to retry only on server errors, without writing a manual status check:

.. code-block:: python

    from ahttp_client import HTTPServerError, retry

    class GithubService(AsyncSession):
        async def after_request(self, response: Response) -> Response:
            response.raise_for_status()
            return response

        @retry(retry_on=(HTTPServerError,))
        @get("/users/{user}/repos")
        async def list_repositories(self, response: Response, user: Annotated[str, Path]):
            return response.json()

Reference
---------

.. autoclass:: ahttp_client.exception.HTTPException()
    :members:

.. autoclass:: ahttp_client.exception.HTTPClientError()
    :show-inheritance:

.. autoclass:: ahttp_client.exception.HTTPServerError()
    :show-inheritance:

.. autofunction:: ahttp_client.exception.exception_for_status
