=====
Retry
=====
A request can be repeated automatically when it fails, using exponential backoff between attempts.
This is configured with the `@retry` decorator, which can be stacked on a request method the same way as `@AsyncSession.single_session` or a hook decorator.

.. code-block:: python
    :linenos:
    :caption: Retry Example

    from typing import Annotated, Any

    from ahttp_client import (
        AsyncSession,
        HTTPServerError,
        Path,
        Response,
        get,
        retry,
    )


    class GitHubService(AsyncSession):
        async def after_request(self, response: Response) -> Response:
            response.raise_for_status()
            return response

        @retry(
            max_retries=3,
            backoff_factor=0.5,
            retry_on=(HTTPServerError, TimeoutError),
            max_delay=4.0,
        )
        @get("/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

`Response.raise_for_status()` turns a 4xx or 5xx response into the matching :class:`HTTPException <ahttp_client.exception.HTTPException>` subclass (see :doc:`exception`), which is what makes such a response eligible for `retry_on` in the first place. Without calling it, a failed response is returned normally and no exception is raised for `retry` to catch.

Backoff and Retry Scope
------------------------
By default, up to three attempts are retried after the initial request, using `HTTPServerError` (any 5xx response) as the triggering exception.

The wait before retry attempt `n` is `backoff_factor * 2 ** (n - 1)` seconds, capped by `max_delay` when it is set. With the defaults above (`backoff_factor=0.5`, `max_delay=4.0`), the delays are `0.5`, `1.0`, `2.0`, and `4.0` (capped) seconds.

Pass one exception class or a tuple of exception classes through `retry_on` to include transport-level failures (such as `TimeoutError`) alongside, or instead of, `HTTPServerError`.

.. warning:: Only exceptions raised during request transport or the session-level `after_request()` hook are eligible for retry. A request-level `after_hook` (see :doc:`hooking`) always runs after the retry operation has finished, so an exception raised there is never retried.

.. note:: `max_retries`, `backoff_factor`, and `max_delay` must all be finite, non-negative values; invalid values raise `TypeError` or `ValueError` when `@retry` is applied.

Decoration Order
-----------------
`@retry` can be placed above or below `@request` (or `@get`, `@post`, etc.) on the same method; both orders attach the same retry configuration:

.. code-block:: python

    # @retry above @request: applied directly to the built RequestCore.
    @retry(max_retries=5, backoff_factor=0.2)
    @get("/users/{user}/repos")
    async def list_repositories(self, response: Response, user: Annotated[str, Path]):
        return response.json()

    # @retry below @request: stashed until @request builds the RequestCore.
    @get("/users/{user}/repos")
    @retry(max_retries=5, backoff_factor=0.2)
    async def list_repositories(self, response: Response, user: Annotated[str, Path]):
        return response.json()

Reference
---------

.. autoclass:: ahttp_client.retry.RetryConfig()
    :members:

.. autodecorator:: ahttp_client.retry.retry
