=========
Exception
=========
`ahttp_client` provides a ready-made exception class for every standard HTTP 4xx/5xx status code, so error handling does not require checking `response.status` manually and raising a custom exception.

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

`Response.raise_for_status()` looks up the exception class registered for the response's status code and raises it, response attached, if it finds one. A successful or redirect response (2xx/3xx) passes through untouched.

Request Status Validation
-------------------------
Set ``raise_on=True`` on ``@request`` or an HTTP method decorator when an
endpoint accepts only HTTP 200. The request execution path validates the raw
response before it is returned or deserialized. Every other status raises an
exception carrying that response: 4xx and 5xx responses use their registered
subclass (or ``HTTPClientError``/``HTTPServerError``), while other statuses use
the base ``HTTPException``. The response is closed before the exception is
raised.

.. code-block:: python

    class GithubService(AsyncSession):
        @get("/health", raise_on=True)
        async def health(self) -> None:
            ...

Unlike ``Response.raise_for_status()``, ``raise_on=True`` rejects all statuses
other than 200, including successful alternatives such as 201 or 204 and
redirects.

Exception Hierarchy
--------------------
Every exception inherits from :class:`HTTPException <ahttp_client.exception.HTTPException>`, which carries the `response` that triggered it along with its `status` code and `url`.

* **HTTPClientError** - the base class for 4xx responses, used directly whenever a 4xx status has no dedicated class of its own.
* **HTTPServerError** - the base class for 5xx responses, used the same way.
* Beyond those two, there is one concrete subclass per standard status code: `HTTPBadRequest` (400), `HTTPNotFound` (404), `HTTPTooManyRequests` (429), `HTTPInternalServerError` (500), `HTTPServiceUnavailable` (503), and so on.

.. note:: RFC 9110 renamed a few statuses; both the current and legacy names are exported as aliases of the same class: `HTTPPayloadTooLarge`/`HTTPContentTooLarge` (413), `HTTPRequestURITooLong`/`HTTPURITooLong` (414), and `HTTPUnprocessableEntity`/`HTTPUnprocessableContent` (422).

Catching by category instead of exact status code comes in handy when every 4xx (or every 5xx) response should be retried or logged the same way:

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
Because `raise_for_status()` turns a failing response into a typed exception, that exception can be listed directly in `retry_on` (see :doc:`retry`) to retry only on server errors, without a manual status check:

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

``raise_on=True`` performs the same typed conversion for 4xx and 5xx statuses
while also rejecting every non-200 status, so it can be used directly with the
default ``retry_on=(HTTPServerError,)`` configuration:

.. code-block:: python

    @retry(max_retries=3)
    @get("/health", raise_on=True)
    async def health(self, response: Response):
        return response.json()

Use ``retry_on_status`` instead when the response should be retried without
raising an exception; see :doc:`retry`.

Reference
---------

.. autoclass:: ahttp_client.exception.HTTPException()
    :members:

.. autoclass:: ahttp_client.exception.HTTPClientError()
    :show-inheritance:

.. autoclass:: ahttp_client.exception.HTTPServerError()
    :show-inheritance:

.. autofunction:: ahttp_client.exception.exception_for_status
