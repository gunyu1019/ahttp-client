# ahttp-client

![PyPI - Version](https://img.shields.io/pypi/v/ahttp-client?style=flat)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ahttp-client?style=flat)
![PyPI - License](https://img.shields.io/pypi/l/ahttp-client?style=flat)

`ahttp-client` is a decorator-based HTTP client framework
that maps typed function parameters to HTTP requests.

### Key Features

- Declare HTTP endpoints using `@request` or the `@get`, `@post`, `@put`,
  `@patch`, `@delete`, and `@options` decoration methods.
- Use `typing.Annotated` to set HTTP parameters such as the path, query, header, or body values.
- Serialize typed request models and deserialize responses using registered codecs.
- Retry failed requests with configurable exception filters and exponential backoff.
- Customize the request lifecycle using `before_hook` and `after_hook` decorators.
- Swap between aiohttp, httpx, and requests without changing how a service is declared.

## Installation

Install the extra for the HTTP client library you want to use.
Python 3.11 or later is required.

```bash
pip install "ahttp-client[aiohttp]"
pip install "ahttp-client[httpx]"
pip install "ahttp-client[requests]"
```

Include the `pydantic` extra to serialize and deserialize Pydantic models.

```bash
pip install "ahttp-client[aiohttp,pydantic]"
```

## Quick start

| Style | Supported client classes | Session class |
| --- | --- | --- |
| Async | `aiohttp.ClientSession`, `httpx.AsyncClient` | `AsyncSession` |
| Sync | `requests.Session`, `httpx.Client` | `Session` |

### Asynchronous Client
Declare a service by extending `AsyncSession`, then decorate coroutine methods
with an HTTP method and path. `Annotated` parameters determine where values are
placed in the request.

```python
import asyncio
from typing import Annotated, Any

import aiohttp

from ahttp_client import AsyncSession, Path, Response, get


class GitHubService(AsyncSession):
    def __init__(self):
        super().__init__("https://api.github.com", aiohttp.ClientSession)

    @get("/users/{user}/repos")
    async def list_repositories(
        self, response: Response, user: Annotated[str, Path]
    ) -> list[dict[str, Any]]:
        return response.json()


async def main():
    async with GitHubService() as service:
        repositories = await service.list_repositories(user="gunyu1019")
        print(repositories)


asyncio.run(main())
```

`AsyncSession` closes its underlying HTTP client when the `async with` block
ends. Decorated responses are also closed automatically after the handler
returns.

### Synchronous Client

Use `Session` and a regular function with `requests.Session` or `httpx.Client`.

```python
from typing import Annotated, Any

import requests

from ahttp_client import Path, Response, Session, get


class GitHubService(Session):
    def __init__(self):
        super().__init__("https://api.github.com", requests.Session)

    @get("/users/{user}/repos")
    def list_repositories(
        self, response: Response, user: Annotated[str, Path]
    ) -> list[dict[str, Any]]:
        return response.json()


with GitHubService() as service:
    repositories = service.list_repositories(user="gunyu1019")
    print(repositories)
```

### Request components

Use `Annotated` to describe dynamic request values.

```python
from typing import Annotated

from ahttp_client import BodyJson, Header, Path, Query, Response, post


class UserService(AsyncSession):
    @post("/users/{user_id}")
    async def update_user(
        self,
        response: Response,
        user_id: Annotated[int, Path],
        verbose: Annotated[bool, Query],
        authorization: Annotated[str, Header.custom_name("Authorization")],
        display_name: Annotated[str, BodyJson.custom_key("profile.displayName")],
    ) -> dict:
        return response.json()
```

| Component | Request location |
| --- | --- |
| `Path` | A `{placeholder}` in the path |
| `Query` | Query string |
| `Header` | Request header |
| `BodyJson` | JSON body field; supports nested keys |
| `BodyForm` | URL-encoded or multipart form field |
| `Body` | Complete raw or JSON request body |

Set `directly_response=True` on a request (or a session) when you need the
`Response` object itself instead of running the decorated handler. In that
case, close it yourself with `await response.async_close()` for async clients
or `response.close()` for sync clients.

### Model serialization

Registered codecs can convert a complete `Body` parameter before transport and
validate a direct response from its return annotation. When Pydantic is
installed, `BaseModel` types and nested model containers are supported
automatically.

Use `@serialize` and `@deserialize` to pass codec options. If the model argument
is omitted, the request body and return annotations select the codec after the
request decorator is applied.

```python
from typing import Annotated

from pydantic import BaseModel

from ahttp_client import AsyncSession, Body, post
from ahttp_client.serializer import deserialize, serialize


class CreateUser(BaseModel):
    name: str
    nickname: str | None = None


class User(BaseModel):
    id: int
    name: str


class UserService(AsyncSession):
    @post("/users", directly_response=True)
    @serialize(exclude_none=True)
    @deserialize(strict=True)
    async def create_user(
        self,
        user: Annotated[CreateUser, Body],
    ) -> User:
        ...
```

In this example, the request body is produced with
`BaseModel.model_dump(mode="json", exclude_none=True)`, and the JSON response is
validated as `User`. Because `directly_response=True` selects deserialized mode
from the registered return type, the decorated method body is not executed.
Pass a model explicitly, such as `@serialize(CreateUser)`, when it cannot be
inferred from an annotation.

### Static type checking

The package includes an optional mypy plugin for declarative endpoint methods.
It preserves their public call signatures and allows a skipped direct-response
body to contain only `...` or `pass`, including when mypy strict mode is used.
No additional package is required:

```ini
[mypy]
plugins = ahttp_client.mypy
```

When Pydantic models are also checked, both installed plugins can be enabled:

```ini
[mypy]
plugins = pydantic.mypy, ahttp_client.mypy
```

### Retries

Use `@retry` to repeat a request when a selected exception is raised. By
default, `HTTPServerError` retries HTTP 5xx failures up to three times after
the initial request. Call `Response.raise_for_status()` from `after_request()`
when HTTP error responses should participate in retry handling.

```python
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
```

The wait before retry attempt `n` is
`backoff_factor * 2 ** (n - 1)` seconds and is capped by `max_delay` when set.
Pass one exception class or a tuple through `retry_on` to include transport or
application failures.

Exceptions raised during request transport or the session-level
`after_request()` hook are eligible for retry. Request-level `after_hook`
callbacks run after the retry operation and are not retried. Retry counts and
delays must be finite, non-negative values.

Retries are enabled automatically only for idempotent HTTP methods. Retrying a
POST, PATCH, or another non-idempotent request can duplicate a server-side
operation, so it requires an explicit `retry_unsafe=True` opt-in:

```python
@retry(max_retries=1, retry_unsafe=True)
@post("/jobs")
async def create_job(self, payload: Annotated[dict[str, Any], BodyJson]) -> None:
    ...
```

### Hooks

Attach a hook to a decorated request to modify it before dispatch or transform
its result afterward. Async requests require async hooks; sync requests require
regular functions.

```python
class GitHubService(AsyncSession):
    @get("/user")
    async def current_user(self, response: Response) -> dict:
        return response.json()

    @current_user.before_hook
    async def add_authorization(self, request, path):
        request.headers["Authorization"] = "Bearer <token>"
        return request, path
```

Override `before_request()` or `after_request()` on `AsyncSession` or `Session`
to apply the same behavior to every request in a service.

## Documentation

- [English documentation](https://gunyu1019.github.io/ahttp-client/en/)
- [한국어 문서](https://gunyu1019.github.io/ahttp-client/ko/)
