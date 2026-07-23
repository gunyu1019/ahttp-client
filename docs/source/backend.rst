=======
Backend
=======
A backend is the adapter layer that lets `ahttp_client` drive different third-party HTTP client libraries through one common interface.
A backend is never instantiated directly; instead, the underlying HTTP client class is passed to a session, and the matching backend is selected automatically.

.. code-block:: python

    import aiohttp
    import httpx

    # Selects AiohttpBackend
    aiohttp_service = GithubService("https://api.github.com", aiohttp.ClientSession)

    # Selects HttpXAsyncSession
    httpx_service = GithubService("https://api.github.com", httpx.AsyncClient)

Supported Backends
-------------------

.. list-table::
    :header-rows: 1

    * - Library
      - Session class
      - Backend class
      - Extra dependency
    * - aiohttp
      - `aiohttp.ClientSession`
      - :class:`ahttp_client.backend.AiohttpBackend`
      - `pip install aiohttp`
    * - httpx (async)
      - `httpx.AsyncClient`
      - :class:`ahttp_client.backend.HttpXAsyncSession`
      - `pip install httpx`
    * - httpx (sync)
      - `httpx.Client`
      - :class:`ahttp_client.backend.HttpXSyncSession`
      - `pip install httpx`
    * - requests (sync)
      - `requests.Session`
      - :class:`ahttp_client.backend.RequestsBackend`
      - `pip install requests`

`AsyncSession` accepts `aiohttp.ClientSession`, `httpx.AsyncClient`, or any other registered asynchronous session class.
`Session` accepts `httpx.Client`, `requests.Session`, or any other registered synchronous session class.

.. note:: An optional dependency (`aiohttp`, `httpx`, or `requests`) that is not installed is simply skipped: `ahttp_client.backend` only exports the backends whose third-party package is importable.

How Backend Selection Works
-----------------------------
:class:`~ahttp_client.backend.BaseBackend` keeps a registry that maps a third-party session class to its backend class.
A concrete backend registers itself automatically once both `session_cls` and `response_cls` are defined on it, through `__init_subclass__`.

When a session such as `AsyncSession(base_url, aiohttp.ClientSession)` is created, it calls `AsyncBackend.from_session(aiohttp.ClientSession, base_url=base_url, **kwargs)`, which looks up the registered backend for that session class and instantiates it.
This is why the same `session=...` argument used for `AsyncSession`/`Session` is simply the third-party client class, not a backend instance.

Writing a Custom Backend
--------------------------
A custom HTTP client library can be supported by subclassing :class:`~ahttp_client.backend.AsyncBackend` (for an asynchronous client) or :class:`~ahttp_client.backend.SyncBackend` (for a synchronous client), setting `session_cls`/`response_cls`, and implementing the abstract methods that:

* Convert a :class:`~ahttp_client.request.RequestCore` into that client's request keyword arguments (`get_request_kwargs`).
* Read status code, headers, URL, body, and closed state from that client's response object (`response_status`, `response_headers`, `response_url`, `response_data`, `response_text`, `response_json`, `response_closed`).
* Close a response and the session itself (`response_close`, `session_close`, `session_closed`).
* Issue each HTTP method against the underlying session (`session_request`, `session_get`, `session_post`, `session_options`, `session_delete`, `session_patch`, `session_put`).

.. code-block:: python
    :linenos:

    from ahttp_client.backend import AsyncBackend

    class MyClientBackend(AsyncBackend):
        session_cls = my_client.Session
        response_cls = my_client.Response

        def get_request_kwargs(self, request_obj):
            ...

        def response_status(self, response_obj) -> int:
            return response_obj.status_code

        # ... remaining abstract methods

Once `MyClientBackend` is imported, `AsyncSession(base_url, my_client.Session)` resolves to it automatically; no further registration step is required.

Reference
---------

.. autoclass:: ahttp_client.backend.BaseBackend()
    :members:
    :member-order: groupwise

.. autoclass:: ahttp_client.backend.AsyncBackend()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.backend.SyncBackend()
    :members:
    :show-inheritance:

.. autoclass:: ahttp_client.backend.AiohttpBackend()
    :show-inheritance:

.. autoclass:: ahttp_client.backend.HttpXAsyncSession()
    :show-inheritance:

.. autoclass:: ahttp_client.backend.HttpXSyncSession()
    :show-inheritance:

.. autoclass:: ahttp_client.backend.RequestsBackend()
    :show-inheritance:
