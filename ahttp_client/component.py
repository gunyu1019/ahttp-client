"""MIT License

Copyright (c) 2023-present gunyu1019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp
    from typing import Annotated, Optional, Callable, NoReturn
    from typing_extensions import Self

    from .session import Session
    from .request import request


class EmptyComponent:
    """Dummy object with nothing defined. It only uses on RequestCore."""

    pass


class Component:
    """Based object on Header, Query, Path, Form and Body

    Attributes
    ----------
    component_name: Callable[[str], str]
        Used to define the name of the component name.
        In default case, it can cause an AttributesError.
    """

    def __init__(self):
        self.component_name: Optional[Callable[[str], str]] = None

    @classmethod
    def custom_name(cls, name: str) -> Self:
        """Define the name of the component(Header, Query, Form and Path)
        Used when the component name must be different from the parameter name.

        Parameters
        ----------
        name: str
            The name of the component (Header, Query, Path and Form)

        Examples
        --------
        >>> @Session.single_session("https://api.yhs.kr")
        ... @request("GET", "/metro/station")
        ... async def station_search_with_query(
        ...     session: Session,
        ...     response: aiohttp.ClientResponse,
        ...     station_name: Annotated[str, Query.custom_name('name')]
        ... ) -> list[...]:
        ...     # A header called "name" is substituted with the value of station_name parameter.
        ...     pass

        Warnings
        --------
        The body component and path component didn't allow the custom_name method to be used.
        """
        new_cls = cls()
        new_cls.component_name = lambda _: name
        return new_cls

    @staticmethod
    def _to_pascal(snake: str) -> str:
        camel = snake.title()
        return re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)

    @staticmethod
    def _to_camel(snake: str) -> str:
        camel = Component._to_pascal(snake)
        return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)

    @classmethod
    def to_camel(cls) -> Self:
        """Define the name of the component(Header, Query, Form and Path) to follow camel case.

        Examples
        --------
        >>> @Session.single_session("https://api.yhs.kr")
        ... @request("GET", "/metro/station")
        ... async def station_search_with_query(
        ...     session: Session,
        ...     response: aiohttp.ClientResponse,
        ...     station_name: Annotated[str, Query.to_camel()]
        ... ) -> list[...]:
        ...     # A header called "stationName" is substituted with the value of station_name parameter.
        ...     pass

        Warnings
        --------
        The body component and path component didn't allow the to_camel method to be used.
        """
        new_cls = cls()
        new_cls.component_name = lambda original_name: new_cls._to_camel(original_name)
        return new_cls

    @classmethod
    def to_pascal(cls) -> Self:
        """Define the name of the component(Header, Query, Form and Path) to follow pascal case.

        Examples
        --------
        >>> @Session.single_session("https://api.yhs.kr")
        ... @request("GET", "/metro/station")
        ... async def station_search_with_query(
        ...     session: Session,
        ...     response: aiohttp.ClientResponse,
        ...     station_name: Annotated[str, Query.to_pascal()]
        ... ) -> list[...]:
        ...     # A header called "StationName" is substituted with the value of station_name parameter.
        ...     pass

        Warnings
        --------
        The body component and path component didn't allow the to_pascal method to be used.
        """
        new_cls = cls()
        new_cls.component_name = lambda original_name: new_cls._to_pascal(original_name)
        return new_cls


class UnsupportedCustomNameComponent(Component):
    @classmethod
    def custom_name(cls, name: str) -> NoReturn:
        raise NotImplementedError("%s.custom_name is not supported." % cls.__name__)

    @classmethod
    def to_camel(cls) -> NoReturn:
        raise NotImplementedError("%s.to_camel is not supported." % cls.__name__)

    @classmethod
    def to_pascal(cls) -> NoReturn:
        raise NotImplementedError("%s.to_pascal is not supported." % cls.__name__)


class Body(UnsupportedCustomNameComponent):
    """This class is used to indicate that a method's parameter is used in the HTTP Request's Body.

    Examples
    --------
    >>> def function(body: dict | Body):
    ...    pass
    """

    pass


class BodyJson(Component):
    """This class defines the parameters of a function used in Body of the HTTP request in dictionary format.

    Examples
    --------
    >>> def function(data: typing.Annotated[str, BodyJson]):
    ...    pass
    """

    pass


class BodyForm(Component):
    """This class defines the parameters of a function to be used in the FormData of an HTTP Request.

    Examples
    --------
    >>> def function(data: str | BodyForm):
    ...    pass
    """

    pass


class Header(Component):
    """This class is used when a function's parameters are used as headers in an HTTP request.

    Examples
    --------
    >>> def function(header: str | Header):
    ...    pass
    """

    DEFAULT_KEY = "__DEFAULT_HEADER__"

    @staticmethod
    def default_header(key: str, value: Any):
        def decorator(func):
            if not hasattr(func, Header.DEFAULT_KEY):
                setattr(func, Header.DEFAULT_KEY, dict())
            getattr(func, Header.DEFAULT_KEY)[key] = value
            return func

        return decorator


class Path(UnsupportedCustomNameComponent):
    """This class is used when a function's parameters are used as path in an HTTP request.
    The parameters associated with the Path populate a portion of the HTTP URL.

    Examples
    --------
    >>> def function(path: str | Path):
    ...    pass
    """

    pass


class Query(Component):
    """This class is used when a function's parameters are used as query in an HTTP request.

    Examples
    --------
    >>> def function(query: str | Query):
    ...    pass
    """

    DEFAULT_KEY = "__DEFAULT_QUERY__"

    @staticmethod
    def default_query(key: str, value: Any):
        def decorator(func):
            if not hasattr(func, Query.DEFAULT_KEY):
                setattr(func, Query.DEFAULT_KEY, dict())
            getattr(func, Query.DEFAULT_KEY)[key] = value
            return func

        return decorator
