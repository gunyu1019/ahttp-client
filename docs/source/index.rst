============
Introduction
============

.. image:: https://img.shields.io/pypi/v/ahttp-client?style=flat
.. image:: https://img.shields.io/pypi/dm/ahttp-client?style=flat
.. image:: https://img.shields.io/pypi/l/ahttp-client?style=flat

`ahttp-client` is a Python package that provides concise and intuitive asynchronous (and synchronous) HTTP requests using `annotated types <https://docs.python.org/ko/3.9/library/typing.html#typing.Annotated>`_ and `@decorator`\ s.

**Key Features**

* Defining a simple request method with decoration.
* Managing HTTP components using annotated types.
* Providing hooks before and after HTTP calls, with optional retry and exponential backoff (see :doc:`retry`).
* Supporting `aiohttp`, `httpx`, and `requests` as pluggable backends (see :doc:`backend`).
* Serializing and deserializing request/response bodies with `dataclasses`, `pydantic`, or `marshmallow` (see :doc:`serialization`).
* Raising a typed `HTTPException` for 4xx/5xx responses (see :doc:`exception`).

Getting Started
---------------

Implement a `GithubService` class extended with `ahttp_client.AsyncSession`.
Then, create a `list_repositories` method using a request decorator.

An `user` argument define HTTP-component (Path) through annotation types.

.. code-block:: python

    class GithubService(AsyncSession):
        def __init__(self):
            super().__init__("https://api.github.com", aiohttp.ClientSession)

        @request("GET", "/users/{user}/repos")
        async def list_repositories(
            self, response: Response, user: Annotated[str, Path]
        ) -> list[dict[str, Any]]:
            return response.json()

Using the asynchronous context manager(`async with`), create a GithubService instance.

.. code-block:: python

    async with GithubService() as service:
        result = await service.list_repositories(user="gunyu1019")
        print(result)

Client Session in GithubServices are terminated when leave the asynchronous context manager.

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
