import inspect
from asyncio import iscoroutinefunction
from typing import Callable, Coroutine, Any, TypeVar

import aiohttp

from .body import Body
from .header import Header
from .parameter import Parameter
from .requestable import Requestable

T = TypeVar('T')


def request(method: str, path: str, **request_kwargs):
    def decorator(func: Callable[[Requestable, aiohttp.ClientResponse, ...], Coroutine[Any, Any, T]]):
        # method is related to Requestable class.
        func_parameters = inspect.signature(func).parameters
        if len(func_parameters) <= 1:
            raise TypeError("%s missing 1 required parameter: 'self(extends Requestable)'".format(func.__name__))

        if not iscoroutinefunction(func):
            raise TypeError("function %s must be coroutine.")

        request_component = {
            "headers": [],
            "params": []
        }
        request_body_parameter = None
        response_parameter = []

        print(func_parameters)
        for parameter in func_parameters.values():
            # Function's Argument (Header)
            if issubclass(parameter.annotation, Header):
                request_component['headers'].append(parameter)
            # Function's Argument (Query)
            elif issubclass(parameter.annotation, Parameter):
                request_component['params'].append(parameter)
            elif issubclass(parameter.annotation, aiohttp.ClientResponse):
                response_parameter.append(parameter)

            # Function's Argument (Body)
            # Body parameter's types can be dict(json), or aiohttp.FormData
            elif issubclass(parameter.annotation, Body):
                if request_body_parameter is not None:
                    raise TypeError(
                        'Body parameter must be one. (%s, %s)'.format(request_body_parameter.name, parameter.name)
                    )
                elif not issubclass(parameter.annotation, (aiohttp.FormData, dict)):
                    raise TypeError("Body parameter can only have aiohttp.FormData or dict.")
                request_body_parameter = parameter

        async def wrapper(self: Requestable, *args, **kwargs):
            if not isinstance(self, Requestable):
                raise TypeError("Class must inherit from class Requestable")

            url = self.base_url + path

            for kv_key, kv_value in request_component.items():
                if kv_key not in request_kwargs.keys() and len(kv_value) > 0:
                    request_kwargs[kv_key] = {}

                for _parameter in kv_value:
                    request_kwargs[kv_key][_parameter.name] = kwargs.get(_parameter.name) or _parameter.default
            if request_body_parameter is not None:
                if issubclass(request_body_parameter.annotation, aiohttp.FormData):
                    request_kwargs['body'] = kwargs.get(request_body_parameter.name) or request_body_parameter.default
                else:
                    request_kwargs['json'] = kwargs.get(request_body_parameter.name) or request_body_parameter.default

            response = await self.session.request(method, url, **request_kwargs)
            for _parameter in response_parameter:
                kwargs[_parameter.name] = response
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
