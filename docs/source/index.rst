============
Introduction
============

.. image:: https://img.shields.io/pypi/v/ahttp-client?style=flat
.. image:: https://img.shields.io/pypi/dm/ahttp-client?style=flat
.. image:: https://img.shields.io/pypi/l/ahttp-client?style=flat

`ahttp-client` is a Python package that provides concise and intuitive asynchronous (and synchronous) HTTP requests using `annotated types <https://docs.python.org/ko/3.9/library/typing.html#typing.Annotated>`_ and `@decorator`\ s.

**Key Features**

* Declare HTTP endpoints using `request` or the `get`, `post`, `put`, `patch`, `delete`, and `options` decoration methods.
* Manage HTTP components, such as the path, query, header, or body values, using annotated types (see :doc:`component`).
* Customize the request lifecycle before and after an HTTP call, with optional retry and exponential backoff (see :doc:`hooking` and :doc:`retry`).
* Swap between `aiohttp`, `httpx`, and `requests` as pluggable backends without changing how a service is declared (see :doc:`backend`).
* Serialize typed request models and deserialize responses using registered codecs for `dataclasses`, `pydantic`, or `marshmallow` (see :doc:`serialization`).
* Raise a typed `HTTPException` for 4xx/5xx responses (see :doc:`exception`).

Installation
------------
`ahttp-client` requires Python 3.11 or later. Install the extra for the HTTP client library a service will use.

.. code-block:: bash

    pip install "ahttp-client[aiohttp]"
    pip install "ahttp-client[httpx]"
    pip install "ahttp-client[requests]"

Add the `pydantic` extra to serialize and deserialize `pydantic.BaseModel` instances (see :doc:`serialization`).

.. code-block:: bash

    pip install "ahttp-client[aiohttp,pydantic]"

Getting Started
---------------
Two session base classes cover both styles of client:

.. list-table::
    :header-rows: 1

    * - Style
      - Supported client classes
      - Session class
    * - Async
      - `aiohttp.ClientSession`, `httpx.AsyncClient`
      - `AsyncSession`
    * - Sync
      - `requests.Session`, `httpx.Client`
      - `Session`

Asynchronous Client
~~~~~~~~~~~~~~~~~~~
Implement a `GithubService` class extended with `ahttp_client.AsyncSession`.
Then, create a `list_repositories` method using a request decorator.

A `user` argument defines an HTTP component (`Path`) through an annotated type.

.. code-block:: python

    class GithubService(AsyncSession):
        def __init__(self):
            super().__init__("https://api.github.com", aiohttp.ClientSession)

        @request("GET", "/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

Using the asynchronous context manager (`async with`), create a `GithubService` instance.

.. code-block:: python

    async with GithubService() as service:
        result = await service.list_repositories(user="gunyu1019")
        print(result)

The client session inside `GithubService` closes automatically once the asynchronous context manager exits.

Synchronous Client
~~~~~~~~~~~~~~~~~~~
For a synchronous service, extend `Session` instead and use a regular function with `requests.Session` or `httpx.Client`.

.. code-block:: python

    class GithubService(Session):
        def __init__(self):
            super().__init__("https://api.github.com", requests.Session)

        @request("GET", "/users/{user}/repos")
        def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

    with GithubService() as service:
        result = service.list_repositories(user="gunyu1019")
        print(result)

The client session inside `GithubService` closes automatically once the `with` block exits.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Guide

   Introduction <self>
   HTTP Component <component>
   Pre-Hooking / Post-Hooking <hooking>

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Features

   Retry <retry>
   Backend <backend>
   Serialization <serialization>
   Exception <exception>

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   API Reference <api>
   Deprecated <deprecated>
