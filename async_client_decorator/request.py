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

import copy
import inspect
from asyncio import iscoroutinefunction
from typing import TypeVar, Optional, Any

import aiohttp

from ._functools import wraps, wrap_annotations
from ._types import RequestFunction
from .body import Body
from .component import Component
from .form import Form
from .header import Header
from .path import Path
from .query import Query
from .session import Session

T = TypeVar("T")


def _get_kwarg_for_request(
    component: Component,
    path: str,
    request_kwargs: dict[str, Any],
    kwargs: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    # Header
    if "headers" not in request_kwargs.keys():
        request_kwargs["headers"] = {}
    request_kwargs["headers"].update(
        component.fill_keyword_argument_to_component("header", kwargs)
    )

    # Parameter
    if "params" not in request_kwargs.keys():
        request_kwargs["params"] = {}
    request_kwargs["params"].update(
        component.fill_keyword_argument_to_component("query", kwargs)
    )

    # Body
    if component.is_body():
        if component.is_formal_form():
            component.fill_keyword_argument_to_component("form", kwargs)

        body_type = component.body_type
        request_kwargs[body_type] = component.get_body()

    # Path
    path_data = component.fill_keyword_argument_to_component("path", kwargs)
    formatted_path = path.format(**path_data)

    return formatted_path, request_kwargs


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
    header_parameter = header_parameter or list()
    query_parameter = query_parameter or list()
    form_parameter = form_parameter or list()
    path_parameter = path_parameter or list()
    response_parameter = response_parameter or list()

    def decorator(func: RequestFunction):
        # method is related to Requestable class.
        signature = inspect.signature(func)
        func_parameters = signature.parameters

        if len(func_parameters) < 1:
            raise TypeError(
                "%s missing 1 required parameter: 'self(extends Session)'".format(
                    func.__name__
                )
            )

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.".format(func.__name__))

        components = Component()

        components.header.update(getattr(func, Header.DEFAULT_KEY, dict()))
        components.query.update(getattr(func, Query.DEFAULT_KEY, dict()))
        components.form.update(getattr(func, Form.DEFAULT_KEY, dict()))
        components.path.update(getattr(func, Path.DEFAULT_KEY, dict()))

        for parameter in func_parameters.values():
            if hasattr(parameter.annotation, "__args__"):
                annotation = parameter.annotation.__args__
            else:
                annotation = (parameter.annotation,)

            if issubclass(Header, annotation) or parameter.name in header_parameter:
                components.header[parameter.name] = parameter
            elif issubclass(Query, annotation) or parameter.name in query_parameter:
                components.query[parameter.name] = parameter
            elif issubclass(Path, annotation) or parameter.name in path_parameter:
                components.path[parameter.name] = parameter
            elif issubclass(Form, annotation) or parameter.name in form_parameter:
                components.add_form(parameter.name, parameter)
            elif issubclass(Body, annotation) or parameter.name == body_parameter:
                components.set_body(parameter)
            elif (
                issubclass(aiohttp.ClientResponse, annotation)
                or parameter.name in response_parameter
            ):
                components.response.append(parameter.name)

        func.__component_parameter__ = components
        func.__request_path__ = path

        @wraps(func)
        @wrap_annotations(func, delete_key=components.response)
        async def wrapper(self: Session, *args, **kwargs):
            wrapped_components = copy.deepcopy(components)
            if not isinstance(self, Session):
                raise TypeError("Class must inherit from class Session")

            # Add parameters, header, body to request keyword
            formatted_path, _request_kwargs = _get_kwarg_for_request(
                wrapped_components, path, request_kwargs, kwargs
            )

            # Request
            response = await self.request(method, formatted_path, **_request_kwargs)

            # Detect directly response
            if (
                issubclass(signature.return_annotation, aiohttp.ClientResponse)
                or directly_response
                or self.directly_response
            ):
                await response.read()
                return response

            # Fill response to parameter
            for _parameter in wrapped_components.response:
                kwargs[_parameter] = response
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
