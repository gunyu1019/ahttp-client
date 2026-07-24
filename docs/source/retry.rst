=====
Retry
=====
The `@retry` decorator repeats a request automatically when it fails, waiting longer between each attempt.
Stack it on a request method the same way as `@AsyncSession.single_session` or a hook decorator.

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

Retrying depends on `Response.raise_for_status()`: it turns a 4xx or 5xx response into the matching :class:`HTTPException <ahttp_client.exception.HTTPException>` subclass (see :doc:`exception`), and that exception is what `retry_on` catches. Without it, a failed response returns normally, and there is no exception for `retry` to act on.

Backoff and Retry Scope
------------------------
The defaults retry up to three times after the initial request, triggered by `HTTPServerError` (any 5xx response).

The wait before retry attempt `n` is `backoff_factor * 2 ** (n - 1)` seconds, capped by `max_delay` when it is set. With the defaults above (`backoff_factor=0.5`, `max_delay=4.0`), the delays are `0.5`, `1.0`, `2.0`, and `4.0` (capped) seconds.

`retry_on` also accepts a tuple, so transport-level failures such as `TimeoutError` can be added alongside `HTTPServerError`, or used in its place.

.. warning:: Retries only cover exceptions from request transport or the session-level `after_request()` hook. A request-level `after_hook` (see :doc:`hooking`) runs after the retry operation is already done, so anything it raises never gets retried.

.. note:: `max_retries`, `backoff_factor`, and `max_delay` all need to be finite, non-negative values. Bad values raise `TypeError` or `ValueError` as soon as `@retry` is applied.

.. warning:: Automatic retries are limited to idempotent HTTP methods. Retrying a POST, PATCH, or another non-idempotent request can duplicate a server-side operation, so it must be explicitly enabled with `retry_unsafe=True`.

Decoration Order
-----------------
`@retry` works whether it sits above or below `@request` (or `@get`, `@post`, etc.) on the same method — both orders end up with the same retry configuration:

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
