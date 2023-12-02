import copy
import inspect
from asyncio import iscoroutinefunction
from typing import TypeVar, Optional

import aiohttp

from ._functools import wraps, wrap_annotations
from ._types import RequestFunction
from .body import Body
from .component import Component
from .form import Form
from .header import Header
from .query import Query
from .session import Session

T = TypeVar("T")


def request(
        method: str,
        path: str,
        directly_response: bool = False,
        header_parameter: list[str] = None,
        query_parameter: list[str] = None,
        form_parameter: list[str] = None,
        body_parameter: Optional[str] = None,
        response_parameter: list[str] = None,
        **request_kwargs
):
    header_parameter = header_parameter or list()
    query_parameter = query_parameter or list()
    form_parameter = form_parameter or list()
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

        component_func_parameter = Component()

        component_func_parameter.header.update(
            getattr(func, Header.DEFAULT_KEY, dict())
        )
        component_func_parameter.query.update(getattr(func, Query.DEFAULT_KEY, dict()))
        component_func_parameter.form.update(getattr(func, Form.DEFAULT_KEY, dict()))

        for parameter in func_parameters.values():
            if hasattr(parameter.annotation, "__args__"):
                annotation = parameter.annotation.__args__
            else:
                annotation = (parameter.annotation,)

            if issubclass(Header, annotation) or parameter.name in header_parameter:
                component_func_parameter.header[parameter.name] = parameter
            elif issubclass(Query, annotation) or parameter.name in query_parameter:
                component_func_parameter.query[parameter.name] = parameter
            elif issubclass(Form, annotation) or parameter.name in form_parameter:
                component_func_parameter.add_form(parameter.name, parameter)
            elif issubclass(Body, annotation) or parameter.name == body_parameter:
                component_func_parameter.set_body(parameter)
            elif (
                    issubclass(aiohttp.ClientResponse, annotation)
                    or parameter.name in response_parameter
            ):
                component_func_parameter.response.append(parameter.name)

        func.__component_parameter__ = component_func_parameter

        @wraps(func)
        @wrap_annotations(func, delete_key=component_func_parameter.response)
        async def wrapper(self: Session, *args, **kwargs):
            wrapped_component_func_parameter = copy.copy(component_func_parameter)
            if not isinstance(self, Session):
                raise TypeError("Class must inherit from class Session")

            for key1, key2 in {"params": "query", "headers": "header"}.items():
                if key1 not in request_kwargs.keys():
                    request_kwargs[key1] = dict()
                request_kwargs[key1].update(
                    wrapped_component_func_parameter.fill_keyword_argument_to_component(
                        key2, kwargs
                    )
                )

            if wrapped_component_func_parameter.is_body():
                if wrapped_component_func_parameter.is_formal_form():
                    wrapped_component_func_parameter.fill_keyword_argument_to_component(
                        "form", kwargs
                    )
                request_kwargs[
                    wrapped_component_func_parameter.body_type
                ] = wrapped_component_func_parameter.get_body()

            url = self.base_url + path

            response = await self.session.request(method, url, **request_kwargs)
            if (
                    issubclass(signature.return_annotation, aiohttp.ClientResponse)
                    or directly_response
                    or self.directly_response
            ):
                return response

            for _parameter in wrapped_component_func_parameter.response:
                kwargs[_parameter] = response
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
