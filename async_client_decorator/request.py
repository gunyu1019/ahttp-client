import inspect
from asyncio import iscoroutinefunction
from typing import TypeVar, Union

import aiohttp

from ._functools import wraps, wrap_annotations
from ._types import RequestFunction
from .session import Session

T = TypeVar("T")


def request(method: str, path: str, directly_response: bool = False, **request_kwargs):
    def decorator(func: RequestFunction):
        # method is related to Requestable class.
        signature = inspect.signature(func)
        func_parameters = signature.parameters
        if len(func_parameters) <= 1:
            raise TypeError(
                "%s missing 1 required parameter: 'self(extends Session)'".format(
                    func.__name__
                )
            )

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.")

        request_component = {"headers": [], "params": []}
        request_body_parameter: inspect.Parameter | None = None
        response_parameter = []

        for parameter in func_parameters.values():
            if not issubclass(Component, parameter.annotation):
                continue

            annotation = getattr(parameter.annotation, "__args__", None) or tuple(parameter.annotation)


            if request_body_parameter is not None:
                raise TypeError(
                    "Body parameter must be one. (%s, %s)".format(
                    request_body_parameter.name, parameter.name
                    )
                )
            """
            # Function's Argument (Header)
            if issubclass(Header, parameter.annotation):
                request_component["headers"].append(parameter)
            # Function's Argument (Query)
            elif issubclass(Parameter, parameter.annotation):
                request_component["params"].append(parameter)
            elif issubclass(aiohttp.ClientResponse, parameter.annotation):
                response_parameter.append(parameter)

            # Function's Argument (Body)
            # Body parameter's types can be dict(json), or aiohttp.FormData
            elif issubclass(Body, parameter.annotation):
                elif not (issubclass(aiohttp.FormData, parameter.annotation) or issubclass(dict, parameter.annotation)):
                    raise TypeError(
                        "Body parameter can only have aiohttp.FormData or dict."
                    )
                request_body_parameter = parameter
            """

        @wraps(func)
        @wrap_annotations(func, delete_key=[x.name for x in response_parameter])
        async def wrapper(self: Requestable, *args, **kwargs):
            if not isinstance(self, Requestable):
                raise TypeError("Class must inherit from class Requestable")

            url = self.base_url + path

            for kv_key, kv_value in request_component.items():
                if kv_key not in request_kwargs.keys() and len(kv_value) > 0:
                    request_kwargs[kv_key] = {}

                for _parameter in kv_value:
                    request_kwargs[kv_key][_parameter.name] = (
                            kwargs.get(_parameter.name) or _parameter.default
                    )
            if request_body_parameter is not None:
                if issubclass(request_body_parameter.annotation, aiohttp.FormData):
                    request_kwargs["body"] = (
                            kwargs.get(request_body_parameter.name)
                            or request_body_parameter.default
                    )
                else:
                    request_kwargs["json"] = (
                            kwargs.get(request_body_parameter.name)
                            or request_body_parameter.default
                    )

            response = await self.session.request(method, url, **request_kwargs)
            if (
                    issubclass(signature.return_annotation, aiohttp.ClientResponse)
                    or directly_response
                    or self.directly_response
            ):
                return response

            for _parameter in response_parameter:
                kwargs[_parameter.name] = response
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
