=====
Retry
=====
The `@retry` decorator repeats a request automatically when it raises a selected exception or returns a selected HTTP status, waiting longer between each attempt.
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
            retry_on_status=(502, 503, 504),
            max_delay=4.0,
        )
        @get("/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

Exception-based retries use ``retry_on``. Calling
`Response.raise_for_status()` in a session-level ``after_request()`` hook
turns a 4xx or 5xx response into the matching
:class:`HTTPException <ahttp_client.exception.HTTPException>` subclass (see
:doc:`exception`), which ``retry_on`` can catch. Alternatively,
``raise_on=True`` on a request treats every status other than 200 as a
failure before the request result is returned.

Status-based retries use ``retry_on_status`` and do not require an exception
or an ``after_request()`` hook. Use it when a response status itself should
be retried while still allowing the final response to be returned normally:

.. code-block:: python

    @retry(max_retries=3, retry_on_status=(429, 502, 503, 504))
    @get("/users/{user}/repos")
    async def list_repositories(self, response: Response, user: Annotated[str, Path]):
        return response.json()

Backoff and Retry Scope
------------------------
The defaults retry up to three times after the initial request, triggered by
``HTTPServerError``. To make a returned 5xx response raise that exception,
use ``Response.raise_for_status()`` or ``raise_on=True``. ``retry_on_status``
defaults to an empty tuple.

The wait before retry attempt `n` is `backoff_factor * 2 ** (n - 1)` seconds, capped by `max_delay` when it is set. With the defaults above (`backoff_factor=0.5`, `max_delay=4.0`), the delays are `0.5`, `1.0`, `2.0`, and `4.0` (capped) seconds.

``retry_on`` accepts one exception class or a tuple, so transport-level
failures such as ``TimeoutError`` can be added alongside
``HTTPServerError``, or used in its place. ``retry_on_status`` likewise
accepts one HTTP status code or a tuple of status codes from 100 through 599.
Responses from attempts that will be retried are closed automatically. When
the retry budget is exhausted, the final matching-status response is not
pre-closed and proceeds through normal response handling.

.. warning:: Exception retries cover failures from request transport, a
   session-level ``after_request()`` hook, and ``raise_on=True`` validation.
   Status retries inspect the response before request-level ``after_hook``
   callbacks run. A request-level ``after_hook`` (see :doc:`hooking`) runs
   after the retry operation is already done, so anything it raises never gets
   retried.

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
