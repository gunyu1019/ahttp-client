"""MIT License

Copyright (c) 2023 gunyu1019

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

try:
    import pydantic
except (ModuleNotFoundError, ImportError):
    is_pydantic = False
else:
    is_pydantic = True

import copy
import inspect
import aiohttp
from asyncio import iscoroutinefunction
from typing import TypeVar, Optional, Any


from ._functools import wraps, wrap_annotations
from ._types import RequestFunction
from .body import Body
from .component import Component
from .form import Form
from .header import Header
from .path import Path
from .query import Query
from .session import Session
from .utils import *

T = TypeVar("T")


class RequestObj:
    def __init__(
            self,
            func: RequestFunction,
            path: str,
            directly_response: bool = False,
            **kwargs
    ):
        self.func = func
        self.path = path
        self.directly_response = directly_response

        # Component for request
        header_parameter = kwargs.get("header_parameter") or list()
        query_parameter = kwargs.get("query_parameter") or list()
        path_parameter = kwargs.get("path_parameter") or list()
        form_parameter = kwargs.get("form_parameter") or list()
        response_parameter = kwargs.get("response_parameter") or list()

        self.component = Component()

        # method is related to Requestable class.
        signature = inspect.signature(self.func)
        func_parameters = signature.parameters

        if len(func_parameters) < 1:
            raise TypeError(
                "%s missing 1 required parameter: 'self(extends Session)'".format(
                    self.func.__name__
                )
            )

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.".format(func.__name__))

    def __call__(self, *args, **kwargs):
        pass

    @property
    def __component_parameter__(self) -> Component:
        return self.component
        # func.__component_parameter__ = components
        # func.__request_path__ = path


def request(
    method: str,
    path: str,
    directly_response: bool = False,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs
):
    """A decoration for making request.
    Create a HTTP client-request, when decorated function is called.

    Parameters
    ----------
    method: str
        HTTP method (example. GET, POST)
    path: str
        Request path. Path connects to the base url.
    directly_response: bool
        Returns a `aiohttp.ClientResponse` without executing the function's body statement.
    header_parameter: list[str]
        Function parameter names used in the header
    query_parameter: list[str]
        Function parameter names used in the query(parameter)
    form_parameter: list[str]
        Function parameter names used in body form.
    path_parameter: list[str]
        Function parameter names used in the path.
    body_parameter: str
        Function parameter name used in the body.
        The body parameter must take only dict, list, or aiohttp.FormData.
    response_parameter: list[str]
        Function parameter name to store the HTTP result in.
    **request_kwargs

    Warnings
    --------
    Form_parameter and Body Parameter can only be used with one or the other.
    """
    return Req(
        lambda self, _path, **kwargs: self.request(method, _path, **kwargs),
        path,
        directly_response,
        header_parameter,
        query_parameter,
        form_parameter,
        path_parameter,
        body_parameter,
        response_parameter,
        **request_kwargs
    )