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

from __future__ import annotations

try:
    import pydantic
except (ModuleNotFoundError, ImportError):
    is_pydantic = False
else:
    is_pydantic = True

import aiohttp
import copy
import inspect
from asyncio import iscoroutinefunction
from typing import TypeVar, Optional, Any, Literal, TYPE_CHECKING

from .body import Body
from .form import Form
from .header import Header
from .path import Path
from .query import Query
from .utils import *

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing_extensions import Self
    from ._types import (
        RequestFunction,
        RequestBeforeHookFunction,
        RequestAfterHookFunction,
    )
    from .session import Session

T = TypeVar("T")


class RequestCore:
    def __init__(
        self,
        func: RequestFunction,
        method: str,
        path: str,
        *,
        name: str = None,
        directly_response: bool = False,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        body: Optional[Collection[Any] | aiohttp.FormData] = None,
        response_parameter: Optional[list[str]] = None,
        **kwargs,
    ):
        self.func = func
        self.session: Session = NotImplemented
        self.method = method

        # Function Wrapper
        self.__qualname__ = func.__qualname__
        self.__module__ = func.__module__
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

        self.request_kwargs = kwargs

        self.name = name or self.func.__name__
        self.path = path
        self.directly_response = directly_response

        self._signature = inspect.signature(self.func)

        # method is related to Session class.
        if len(self._signature.parameters) < 1:
            raise TypeError(
                "%s missing 1 required parameter: 'self(extends Session)'".format(
                    self.func.__name__
                )
            )

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.".format(func.__name__))

        # Components
        self.params: dict[str, Any] = params or dict()
        self.headers: dict[str, Any] = headers or dict()
        self.body: Optional[aiohttp.FormData | Collection[Any]] = body

        # Components (Function Parameter)
        self.header_parameter: dict[str, inspect.Parameter] = dict()
        self.query_parameter: dict[str, inspect.Parameter] = dict()
        self.path_parameter: dict[str, inspect.Parameter] = dict()
        self.body_form_parameter: dict[str, inspect.Parameter] = dict()

        self.body_parameter_type: Literal["json", "data"] | None = None
        self.body_parameter: Optional[inspect.Parameter] = None

        self.response_parameter: list[str] = response_parameter or list()

        self._before_hook: Optional[RequestBeforeHookFunction] = None
        self._after_hook: Optional[RequestAfterHookFunction] = None

    @classmethod
    def from_decorator(
        cls,
        func: RequestFunction,
        method: str,
        path: str,
        *,
        query_parameter: Optional[list[str]] = None,
        header_parameter: Optional[list[str]] = None,
        form_parameter: Optional[list[str]] = None,
        path_parameter: Optional[list[str]] = None,
        body_parameter: Optional[str] = None,
        **kwargs,
    ) -> Self:
        new_cls = cls(func, method, path, **kwargs)

        # Setup
        new_cls._add_parameter_to_component(
            query_parameter=query_parameter or list(),
            header_parameter=header_parameter or list(),
            form_parameter=form_parameter or list(),
            body_parameter=body_parameter,
            path_parameter=path_parameter or list(),
        )
        new_cls._add_private_key()
        new_cls._delete_response_annotation()
        return new_cls

    def copy(self) -> Self:
        new_cls = RequestCore(
            self.func,
            self.method,
            self.path,
            name=self.name,
            directly_response=self.directly_response,
            headers=self.headers,
            params=self.params,
            body=self.body,
            response_parameter=self.response_parameter,
            **self.request_kwargs,
        )

        new_cls.header_parameter = self.header_parameter
        new_cls.query_parameter = self.query_parameter
        new_cls.path_parameter = self.path_parameter
        new_cls.body_form_parameter = self.body_form_parameter

        new_cls.body_parameter_type = self.body_parameter_type
        new_cls.body_parameter = self.body_parameter

        new_cls._before_hook = self._before_hook
        new_cls._after_hook = self._after_hook

        new_cls._delete_response_annotation()
        return new_cls

    def before_hook(self, func: RequestBeforeHookFunction):
        self._before_hook = func
        return func

    def after_hook(self, func: RequestAfterHookFunction):
        self._after_hook = func
        return func

    @property
    def is_body(self) -> bool:
        return (
            self.body_parameter is not None
            or self.is_formal_form
            or self.body is not None
        )

    @property
    def is_formal_form(self) -> bool:
        return len(self.body_form_parameter) > 0

    @property
    def body_type(self) -> Optional[Literal["json", "data"]]:
        if isinstance(self.body, aiohttp.FormData):
            return "data"
        elif self.body is None:
            return
        if self.body_parameter_type is not None:
            return self.body_parameter_type
        return "json"

    def _duplicated_check_body(self):
        if self.body is not None and self.body_parameter is not None:
            raise TypeError("Only one Body Parameter or Body is allowed.")

    def _duplicated_check_body_parameter(self):
        if self.body_parameter is not None or len(self.body_form_parameter) > 0:
            raise TypeError("Duplicated Form Parameter or Body Parameter.")

    @staticmethod
    def _check_body_type(parameter: inspect.Parameter):
        body_annotation = parameter.annotation
        argument = (
            body_annotation.__args__
            if is_annotated_parameter(body_annotation)
            else body_annotation
        )
        separated_argument = separate_union_type(argument)
        origin_argument = [
            get_origin_for_generic(x) for x in make_collection(separated_argument)
        ]

        if is_subclass_safe(origin_argument, (Collection, aiohttp.FormData)):
            return
        raise TypeError("Body parameter can only have aiohttp.FormData or Collection.")

    def _add_private_key(self):
        self.headers.update(getattr(self.func, Header.DEFAULT_KEY, dict()))
        self.params.update(getattr(self.func, Query.DEFAULT_KEY, dict()))

    def _add_parameter_to_component(
        self,
        *,
        query_parameter: Optional[list[str]] = None,
        header_parameter: Optional[list[str]] = None,
        form_parameter: Optional[list[str]] = None,
        body_parameter: Optional[str] = None,
        path_parameter: Optional[list[str]] = None,
    ):
        for parameter in self._signature.parameters.values():
            annotation = parameter.annotation
            metadata = (
                annotation.__metadata__
                if is_annotated_parameter(annotation)
                else annotation
            )
            separated_annotation = separate_union_type(metadata)
            # for annotation in separated_annotation:
            #     pass

            if (
                is_subclass_safe(separated_annotation, Header)
                or parameter.name in header_parameter
            ):
                self.header_parameter[parameter.name] = parameter
            elif (
                is_subclass_safe(separated_annotation, Query)
                or parameter.name in query_parameter
            ):
                self.query_parameter[parameter.name] = parameter
            elif (
                is_subclass_safe(separated_annotation, Path)
                or parameter.name in path_parameter
            ):
                self.path_parameter[parameter.name] = parameter
            elif (
                is_subclass_safe(separated_annotation, Form)
                or parameter.name in form_parameter
            ):
                self._duplicated_check_body_parameter()
                self.body_parameter_type = "data"
                self.body_form_parameter[parameter.name] = parameter
                self._duplicated_check_body()
            elif (
                is_subclass_safe(separated_annotation, Body)
                or parameter.name == body_parameter
            ):
                self._check_body_type(parameter)
                self._duplicated_check_body_parameter()
                if is_subclass_safe(separated_annotation, aiohttp.FormData):
                    self.body_parameter_type = "data"
                else:
                    self.body_parameter_type = "json"
                self.body_parameter = parameter
                self._duplicated_check_body()
            elif is_subclass_safe(separated_annotation, aiohttp.ClientResponse):
                self.response_parameter.append(parameter.name)

    def _delete_response_annotation(self):
        parameter_without_return_annotation = []
        for parameter in self._signature.parameters.values():
            if parameter.name in self.response_parameter:
                continue

            parameter_without_return_annotation.append(parameter)

        self._signature = self._signature.replace(
            parameters=parameter_without_return_annotation
        )

    def _fill_parameter(self, bounded_argument: dict[str, Any]):
        # Header
        for _name, _parameter in self.header_parameter.items():
            self.headers[_name] = bounded_argument.get(_parameter.name)

        # Parameter
        for _name, _parameter in self.query_parameter.items():
            self.params[_name] = bounded_argument.get(_parameter.name)

        # Body
        self._duplicated_check_body()
        if self.is_formal_form and self.body_parameter is not None:  # self.is_body
            form_data = aiohttp.FormData()
            for _name, _parameter in self.body_form_parameter.items():
                form_data.add_field(_name, bounded_argument.get(_parameter.name))
            self.body = form_data
        elif self.body_parameter is not None:
            self.body = bounded_argument.get(self.body_parameter.name)

    def get_request_kwargs(self):
        """Get keyword arguments to call request method"""
        request_kwargs = copy.deepcopy(self.request_kwargs)

        # Header
        if len(self.headers) > 0:
            request_kwargs["headers"] = self.headers

        # Parameter
        if len(self.params) > 0:
            request_kwargs["params"] = self.params

        # Body
        if self.is_body:
            request_kwargs[str(self.body_type)] = self.body

        return request_kwargs

    def _get_request_path(self, bounded_argument: dict[str, Any]) -> str:
        formatted_argument = dict()
        for _name, _parameter in self.path_parameter.items():
            formatted_argument[_name] = bounded_argument.get(_parameter.name)
        formatted_path = self.path.format(**formatted_argument)
        return formatted_path

    def __eq__(self, other):
        if not isinstance(other, RequestCore):
            return False
        return (
            other.name == self.name
            and other.func == self.func
            and other.path == self.path
            and other.params == self.params
            and other.headers == self.headers
            and other.body == self.body
            and other.directly_response == self.directly_response
            and other.header_parameter == self.header_parameter
            and other.query_parameter == self.query_parameter
            and other.path_parameter == self.path_parameter
            and other.body_form_parameter == self.body_form_parameter
            and other.body_parameter_type == self.body_parameter_type
            and other.body_parameter == self.body_parameter
            and other._before_hook == self._before_hook
            and other._after_hook == self._after_hook
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self) -> Self:
        return self.copy()

    async def __call__(self, *args, **kwargs):
        if self.session is NotImplemented:
            raise TypeError("Class must inherit from class Session")

        bound_argument = self._signature.bind(self.session, *args, **kwargs)
        bound_argument.apply_defaults()

        req_obj = self.copy()

        req_obj._fill_parameter(bound_argument.arguments)
        formatted_path = req_obj._get_request_path(bound_argument.arguments)

        if self._before_hook is not None:
            req_obj = await self._before_hook(req_obj, formatted_path)
        response = await self.session._make_request(req_obj, formatted_path)
        if self._after_hook is not None:
            response = await self._after_hook(response)

        # Detect directly response
        if self.directly_response and self.session.directly_response:
            if isinstance(response, aiohttp.ClientResponse):
                await response.read()  # Content-Read.
            return response

        for _parameter in self.response_parameter:
            kwargs[_parameter] = response
        kwargs.update(bound_argument.arguments)
        return await self.func(**kwargs)

    @property
    def __request_path__(self) -> str:
        return self.path

    @property
    def __core__(self) -> Self:
        return self


def request(
    method: str,
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
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
    name: Optional[str]
        The name of the Request
    method: str
        HTTP method (example. GET, POST)
    path: str
        Request path. Path connects to the base url.
    params: Optional[dict[str, Any]]
        Request parameters.
    headers: Optional[dict[str, Any]]
        Request headers.
    body: Optional[Collection[Any] | aiohttp.FormData]
        Request body.
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
        The body parameter must take only Collection, or aiohttp.FormData.
    response_parameter: list[str]
        Function parameter name to store the HTTP result in.
    **request_kwargs

    Warnings
    --------
    Form_parameter and Body Parameter can only be used with one or the other.
    """

    def decorator(func):
        return RequestCore.from_decorator(
            func,
            method,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def get(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs,
):
    def decorator(func):
        return RequestCore.from_decorator(
            func,
            aiohttp.hdrs.METH_GET,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def post(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs,
):
    def decorator(func):
        return RequestCore.from_decorator(
            func,
            aiohttp.hdrs.METH_POST,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def options(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs,
):
    def decorator(func):
        return RequestCore.from_decorator(
            func,
            aiohttp.hdrs.METH_OPTIONS,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def put(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs,
):
    def decorator(func):
        return RequestCore.from_decorator(
            func,
            aiohttp.hdrs.METH_PUT,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def delete(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[aiohttp.FormData | Collection[Any]] = None,
    header_parameter: list[str] = None,
    query_parameter: list[str] = None,
    form_parameter: list[str] = None,
    path_parameter: list[str] = None,
    body_parameter: Optional[str] = None,
    response_parameter: list[str] = None,
    **request_kwargs,
):
    def decorator(func):
        return RequestCore.from_decorator(
            func,
            aiohttp.hdrs.METH_DELETE,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator
