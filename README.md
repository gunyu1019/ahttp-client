 # ahttp-client
 
![PyPI - Version](https://img.shields.io/pypi/v/ahttp-client?style=flat)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ahttp-client?style=flat)
![PyPI - License](https://img.shields.io/pypi/l/ahttp-client?style=flat)

An ahttp-client is Python package that provides concise and aintuitive asynchronous HTTP request using [annotated type](https://docs.python.org/ko/3.9/library/typing.html#typing.Annotated) and `@decorator`. 

**Key Feautre**
- Defining a simple request method with decoration.
- Managing HTTP Compoents using Annotated Types.
- Providing Hooks before and after HTTP calls.

## Getting Started

Implement a `GithubService` class extended with `ahttp_client.Session`. 
Then, create a `list_repositories` method using a request decorator.

An `user` argument define HTTP-component (Path) through annotation types.

```python
class GithubService(Session):
    def __init__(self):
        super().__init__("https://api.github.com")

    @request("GET", "/users/{user}/repos")
    def list_repositories(
        user: Annotated[str, Path]
    ) -> dict[str, Any]:
        return 
```

Using the asynchronous context manager(`async with`), create a GithubService instance.

```python
async with GithubService() as service:
    result = await service.list_repoisitories(user = "gunyu1019")
    print(result)
```

Client Session in GithubServices are terminated when leave the asynchronous context manager.

## Documentaion
* English: https://gunyu1019.github.io/ahttp-client/en/
* Korean: https://gunyu1019.github.io/ahttp-client/ko/