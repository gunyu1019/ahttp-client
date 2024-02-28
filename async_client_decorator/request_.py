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
from typing import TypeVar, Optional, Any, Literal

from ._functools import wraps, wrap_annotations
from ._types import RequestFunction, CoroutineFunction
from .body import Body
from .form import Form
from .header import Header
from .path import Path
from .query import Query
from .session import Session
from .utils import *

T = TypeVar("T")


class Request:
    def __init__(
        self,
        func: RequestFunction,
        request_cls: CoroutineFunction[aiohttp.ClientResponse],
        path: str,
        directly_response: bool = False,
        **kwargs,
    ):
        self.func = func
        self.session: Session = NotImplemented
        self.__request_cls = request_cls

        # Function Wrapper
        self.__qualname__ = func.__qualname__
        self.__module__ = func.__module__
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

        self.request_kwargs = kwargs

        self.path = path
        self.directly_response = directly_response

        self._signature = inspect.signature(self.func)
        function_parameters = self._signature.parameters

        # method is related to Session class.
        if len(function_parameters) < 1:
            raise TypeError(
                "%s missing 1 required parameter: 'self(extends Session)'".format(
                    self.func.__name__
                )
            )

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.".format(func.__name__))

        # Components
        self.header_parameter: dict[str, inspect.Parameter | Any] = dict()
        self.query_parameter: dict[str, inspect.Parameter | Any] = dict()
        self.path_parameter: dict[str, inspect.Parameter | Any] = dict()
        self.body_form_parameter: dict[str, inspect.Parameter | Any] = dict()

        self.body_type: Literal["json", "data"] | None = None
        self.body_parameter: Optional[inspect.Parameter] = None

        self.response_parameter: list[str] = list()

        for parameter in function_parameters.values():
            annotation = parameter.annotation
            metadata = (
                annotation.__metadata__
                if is_annotated_parameter(annotation)
                else annotation
            )
            separated_annotation = separate_union_type(metadata)
            # for annotation in separated_annotation:
            #     pass

            if is_subclass_safe(separated_annotation, Header):
                self.header_parameter[parameter.name] = parameter
            elif is_subclass_safe(separated_annotation, Query):
                self.query_parameter[parameter.name] = parameter
            elif is_subclass_safe(separated_annotation, Path):
                self.path_parameter[parameter.name] = parameter
            elif is_subclass_safe(separated_annotation, Form):
                # _duplicated_check_body
                if self.body_type is not None:
                    raise ValueError("Use only one Form Parameter or Body Parameter.")

                self.body_type = "data"
                self.body_form_parameter[parameter.name] = parameter
            elif is_subclass_safe(separated_annotation, Body):
                # _duplicated_check_body
                if self.body_type is not None:
                    raise ValueError("Use only one Form Parameter or Body Parameter.")

                self.body_type = "json"
                self.body_parameter = parameter
            elif is_subclass_safe(separated_annotation, aiohttp.ClientResponse):
                self.response_parameter.append(parameter.name)

        # Delete return annotations
        parameter_without_return_annotation = []
        for parameter in function_parameters.values():
            if parameter.name in self.response_parameter:
                continue

            parameter_without_return_annotation.append(parameter)

        self._signature = self._signature.replace(
            parameters=parameter_without_return_annotation
        )

    def _get_request_kwargs(
            self,
            bounded_argument: dict[str, Any]
    ):
        request_kwargs = copy.deepcopy(self.request_kwargs)

        # Header
        if "headers" not in request_kwargs.keys():
            request_kwargs["headers"] = {}
        for _name, _parameter in self.header_parameter.items():
            request_kwargs["headers"][_name] = bounded_argument.get(_parameter.name)

        # Parameter
        if "params" not in request_kwargs.keys():
            request_kwargs["params"] = {}
        for _name, _parameter in self.query_parameter.items():
            request_kwargs["params"][_name] = bounded_argument.get(_parameter.name)

        # Body
        if self.body_type == 'data':  # self.is_body
            form_data = aiohttp.FormData()
            for _name, _parameter in self.body_form_parameter.items():
                form_data.add_field(
                    _name,
                    bounded_argument.get(_parameter.name)
                )
            request_kwargs[self.body_type] = form_data
        elif self.body_type == 'json':
            request_kwargs[self.body_type] = bounded_argument.get(self.body_parameter.name)

        return request_kwargs

    def _get_request_path(
            self,
            bounded_argument: dict[str, Any]
    ) -> str:
        formatted_argument = dict()
        for _name, _parameter in self.path_parameter.items():
            formatted_argument[_name] = bounded_argument.get(_parameter.name)
        formatted_path = self.path.format(**formatted_argument)
        return formatted_path

    async def __call__(self, *args, **kwargs):
        if self.session is NotImplemented or not isinstance(
            self.session, Session
        ):
            raise TypeError("Class must inherit from class Session")

        bound_argument = self._signature.bind(self.session, *args, **kwargs)

        request_kwargs = self._get_request_kwargs(bound_argument.arguments)
        formatted_path = self._get_request_path(bound_argument.arguments)
        response = await self.__request_cls(self.session, formatted_path, **request_kwargs)

        # Detect directly response
        if self.directly_response and self.session.directly_response:
            await response.read()  # Content-Read.
            return response

        for _parameter in self.response_parameter:
            kwargs[_parameter] = response
        kwargs.update(bound_argument.arguments)
        return await self.func(**kwargs)

    # @property
    # def __component_parameter__(self) -> Component:
    #     return self.component

    @property
    def __request_path__(self) -> str:
        return self.path

    def _bind(self):
        return


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
    **request_kwargs,
):
    """A decoration for making request.
    Create an HTTP client-request, when decorated function is called.

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
    def decorator(func):
        return Request(
            func,
            lambda self, _path, **kwargs: self.request(method, _path, **kwargs),
            path,
            directly_response=directly_response,
            # header_parameter,
            # query_parameter,
            # form_parameter,
            # path_parameter,
            # body_parameter,
            # response_parameter,
            **request_kwargs,
        )
    return decorator
