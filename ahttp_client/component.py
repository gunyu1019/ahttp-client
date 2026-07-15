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

    from .response import Response
    from .session import AsyncSession
    from .request import request


class _EmptyComponent:
    """Internal marker for a parameter without a request component."""

    pass


class Component:
    """Base class for request-parameter components.

    Components can be used in annotations to map a function parameter to a
    header, query string, path placeholder, or request body.

    Attributes
    ----------
    component_name: Callable[[str], str]
        Optional transformation used for the component key sent on the wire.
    """

    def __init__(self):
        self.component_name: Optional[Callable[[str], str]] = None

    @classmethod
    def custom_name(cls, name: str) -> Self:
        """Return a component instance with a fixed transmitted name.

        Parameters
        ----------
        name: str
            Name used in the request instead of the Python parameter name.

        Raises
        ------
        NotImplementedError
            If the component does not support renamed fields, such as
            :class:`Path` or :class:`Body`.
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
        """Return a component instance that converts its key to camel case.

        Raises
        ------
        NotImplementedError
            If the component does not support renamed fields.
        """
        new_cls = cls()
        new_cls.component_name = lambda original_name: new_cls._to_camel(original_name)
        return new_cls

    @classmethod
    def to_pascal(cls) -> Self:
        """Return a component instance that converts its key to Pascal case.

        Raises
        ------
        NotImplementedError
            If the component does not support renamed fields.
        """
        new_cls = cls()
        new_cls.component_name = lambda original_name: new_cls._to_pascal(original_name)
        return new_cls


class _UnsupportedCustomNameComponent(Component):
    @classmethod
    def custom_name(cls, name: str) -> NoReturn:
        raise NotImplementedError("%s.custom_name is not supported." % cls.__name__)

    @classmethod
    def to_camel(cls) -> NoReturn:
        raise NotImplementedError("%s.to_camel is not supported." % cls.__name__)

    @classmethod
    def to_pascal(cls) -> NoReturn:
        raise NotImplementedError("%s.to_pascal is not supported." % cls.__name__)


class _BodyFileComponent(Component):
    def __init__(self):
        super(_BodyFileComponent, self).__init__()
        self.metadata_filename: Optional[str] = None
        self.metadata_content_type: Optional[str] = None

    @classmethod
    def metadata(cls, filename: Optional[str] = None, content_type: Optional[str] = None) -> Self:
        """Configure file metadata for a body value.

        On :class:`BodyForm`, this makes the field a multipart file part. On
        :class:`Body`, the raw body is preserved and the metadata is sent in
        the request-level ``Content-Disposition`` and ``Content-Type``
        headers.

        Parameters
        ----------
        filename: Optional[str]
            File name included in the multipart field.
        content_type: Optional[str]
            MIME type included in the multipart field.
        """
        new_cls = cls()
        new_cls.metadata_filename = filename
        new_cls.metadata_content_type = content_type
        return new_cls

    @property
    def is_file_type(self) -> bool:
        return self.metadata_filename is not None or self.metadata_content_type is not None


class Body(_BodyFileComponent, _UnsupportedCustomNameComponent):
    """Mark a parameter as the complete request body.

    ``dict``, ``list``, and ``tuple`` values are encoded as JSON; other values
    (including file-like values) are sent as raw body data. A ``Body``
    parameter cannot be combined with ``BodyJson`` or ``BodyForm`` parameters.
    :meth:`metadata` adds filename and content-type metadata without changing
    the raw-body encoding.
    """

    pass


class BodyJson(Component):
    """Mark a parameter as a field in a JSON request body.

    Use :meth:`custom_key` to place the value under a different or nested JSON
    key.
    """

    def __init__(self):
        super(BodyJson, self).__init__()
        self.json_key: Optional[str] = None

    @classmethod
    def custom_key(cls, key: str) -> Self:
        """Return a JSON body component with a custom key.

        A dot-separated key creates nested JSON objects.

        Parameters
        ----------
        key: str
            Key used in the JSON request body.
        """
        new_cls = cls()
        new_cls.json_key = key
        return new_cls

    @property
    def depth(self) -> int:
        """Return the number of levels in the custom JSON key."""
        if self.json_key is None:
            return 0
        return self.json_key.count(".") + 1

    @property
    def keys(self) -> list[str]:
        """Return the custom JSON key split into nested key names."""
        if self.json_key is None:
            return []
        return self.json_key.split(".")


class BodyForm(_BodyFileComponent):
    """Mark a parameter as a field in a form request body.

    File-like values, or fields whose :meth:`metadata` configuration specifies
    a filename or content type, use ``multipart/form-data``; other form fields
    default to URL encoding.
    """

    pass


class Header(Component):
    """Mark a parameter as an HTTP request header.

    :meth:`default_header` adds a static header to a decorated request.
    """

    DEFAULT_KEY = "__DEFAULT_HEADER__"

    @staticmethod
    def default_header(key: str, value: Any):
        """Add a static header to a decorated request.

        Parameters
        ----------
        key: str
            Header name.
        value: Any
            Header value.
        """

        def decorator(func):
            if not hasattr(func, Header.DEFAULT_KEY):
                setattr(func, Header.DEFAULT_KEY, dict())
            getattr(func, Header.DEFAULT_KEY)[key] = value
            return func

        return decorator


class Path(_UnsupportedCustomNameComponent):
    """Mark a parameter as a placeholder in the request path.

    The parameter name must match a ``str.format`` placeholder in ``path``.
    """

    pass


class Query(Component):
    """Mark a parameter as an HTTP query-string value.

    :meth:`default_query` adds a static query parameter to a decorated request.
    """

    DEFAULT_KEY = "__DEFAULT_QUERY__"

    @staticmethod
    def default_query(key: str, value: Any):
        """Add a static query parameter to a decorated request.

        Parameters
        ----------
        key: str
            Query parameter name.
        value: Any
            Query parameter value.
        """

        def decorator(func):
            if not hasattr(func, Query.DEFAULT_KEY):
                setattr(func, Query.DEFAULT_KEY, dict())
            getattr(func, Query.DEFAULT_KEY)[key] = value
            return func

        return decorator
