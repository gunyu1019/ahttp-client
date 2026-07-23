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

import copy
import inspect
from abc import ABC, abstractmethod
from urllib.parse import quote
from typing import (
    Any,
    Generic,
    TypeVar,
    TYPE_CHECKING,
    Callable,
    NamedTuple,
    Optional,
    Self,
    cast,
    get_type_hints,
    overload,
)

from ._types import (
    _IO_TYPE,
    _BODY_JSON_TYPE,
    RequestFunction,
    RequestDecorator,
    ValidationDecorator,
    ValidationFunction,
    AsyncRequestBeforeHookFunction,
    AsyncRequestAfterHookFunction,
    SyncRequestBeforeHookFunction,
    SyncRequestAfterHookFunction,
)
from .component import (
    Component,
    _EmptyComponent,
    BodyJson,
    Body,
    BodyForm,
    Header,
    Path,
    Query,
)
from .enum import Method, BodyFormEncoding, BodyType, DirectResponseType
from .response import Response
from .serialization.base import BaseCodec, BaseSerializer, BaseDeserializer
from .session import BaseSession
from .utils import *


class BodyJsonEntry(NamedTuple):
    parameter: inspect.Parameter
    custom_key: Optional[str]


class BodyFormEntry(NamedTuple):
    parameter: inspect.Parameter
    is_file_type: bool
    component: Optional[BodyForm]


class BodyEntry(NamedTuple):
    """Metadata collected for a complete request-body parameter."""

    parameter: inspect.Parameter
    is_file_type: bool
    component: Optional[Body]

    @property
    def name(self) -> str:
        """Return the underlying parameter name for backward compatibility."""
        return self.parameter.name


if TYPE_CHECKING:
    from .request_bound import RequestBound
    from .retry import RetryConfig
    from .session import AsyncSession, Session

HookResultT = TypeVar("HookResultT")
RequestBeforeHookT = TypeVar("RequestBeforeHookT", bound=Callable[..., Any])
RequestAfterHookT = TypeVar("RequestAfterHookT", bound=Callable[..., Any])


class RequestCore(Generic[RequestBeforeHookT, RequestAfterHookT], ABC):
    """Base descriptor for a decorated HTTP request.

    A request core is bound to a :class:`~ahttp_client.session.BaseSession`
    instance when it is accessed as a session attribute.  The bound request
    builds a backend-specific request from its static values and annotated
    function parameters, then executes the decorated function with any
    :class:`~ahttp_client.response.Response` parameter filled in.

    Attributes
    ----------
    name: str
        The name of the request.
    func: Callable[..., Any]
        The synchronous or asynchronous function executed after the response
        is received.
    method: str | Method
        HTTP method.
    path: str
        Path relative to the session base URL, unless the backend manages its
        own base URL.
    directly_response: DirectResponseType | bool
        Return the response-pipeline result without executing the decorated
        function.
    params: dict[str, Any]
        Static query parameters.
    headers: dict[str, Any]
        Static request headers.
    body: Optional[Any]
        Static request body. Its encoding is determined by ``body_type``.
    header_parameter: dict[str, inspect.Parameter]
        Function parameters used as request headers.
    query_parameter: dict[str, inspect.Parameter]
        Function parameters used as query parameters.
    body_json_parameter: dict[str, inspect.Parameter]
        Function parameters collected into a JSON body.
    body_form_parameter: dict[str, inspect.Parameter]
        Function parameters collected into a form body.
    path_parameter: dict[str, inspect.Parameter]
        Function parameters substituted into the path.
    body_parameter: Optional[BodyEntry]
        Metadata for the function parameter used as the complete request body.
    body_parameter_type: Optional[BodyType]
        Explicit body encoding, if one was inferred from the parameter
        annotations or form configuration.
    response_parameter: list[str]
        Names of function parameters that receive the HTTP response.
    request_kwargs: dict[str, Any]
        Keyword arguments passed through to the backend request method.
    """

    __request_core__ = True

    def __init__(
        self,
        func: RequestFunction[..., Any],
        method: str | Method,
        path: str,
        *,
        name: Optional[str] = None,
        directly_response: DirectResponseType | bool = False,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        body: Optional[Any] = None,
        response_parameter: Optional[list[str]] = None,
        **kwargs,
    ):
        self.func = func
        self.method = method

        # Function Wrapper
        self.__qualname__ = func.__qualname__
        self.__module__ = func.__module__
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__annotations__ = func.__annotations__

        self.request_kwargs = kwargs

        self.name = name or self.func.__name__
        self.path = path
        self.directly_response = directly_response

        self._signature = inspect.signature(self.func)

        # method is related to Session class.
        if len(self._signature.parameters) < 1:
            raise TypeError("%s missing 1 required parameter: 'self(extends Session)'" % self.func.__name__)

        # if not iscoroutinefunction(func):
        #     raise TypeError("function %s must be coroutine." % func.__name__)

        # Static HTTP Components
        self.params: dict[str, Any] = params or dict()
        self.headers: dict[str, Any] = headers or dict()
        self.body: Optional[Any] = body
        self._body_file: Optional[Any] = None  # for multipart/form-data file

        # Components (Function Parameter)
        self.header_parameter: dict[str, inspect.Parameter] = dict()
        self.query_parameter: dict[str, inspect.Parameter] = dict()
        self.path_parameter: dict[str, inspect.Parameter] = dict()
        self.body_json_parameter: dict[str, BodyJsonEntry] = dict()
        self.body_form_parameter: dict[str, BodyFormEntry] = dict()
        self.body_form_encoding_type: BodyFormEncoding = BodyFormEncoding.AUTO

        self.body_parameter: Optional[BodyEntry] = None
        self.body_parameter_type: Optional[BodyType] = None

        self.validation_parameter: dict[str, list[ValidationFunction]] = dict()
        self.response_parameter: list[str] = response_parameter or list()

        self._before_hook: Optional[RequestBeforeHookT] = None
        self._after_hook: Optional[RequestAfterHookT] = None

        # Serialization
        self._serializer: Optional[BaseSerializer] = None
        self._deserializer: Optional[BaseDeserializer] = None
        self._body_model_candidates: tuple[Any, ...] = ()
        self._return_model: Any = inspect.Signature.empty

        # Retry
        self._retry_config: Optional[RetryConfig] = None

    @classmethod
    def from_decorator(
        cls,
        func: RequestFunction[..., Any],
        method: str | Method,
        path: str,
        *,
        query_parameter: Optional[list[str]] = None,
        header_parameter: Optional[list[str]] = None,
        body_json_parameter: Optional[list[str]] = None,
        form_parameter: Optional[list[str]] = None,
        form_encoding: Optional[BodyFormEncoding] = None,
        path_parameter: Optional[list[str]] = None,
        body_parameter: Optional[str] = None,
        **kwargs,
    ) -> Self:
        new_cls = cls(func, method, path, **kwargs)

        # Setup
        new_cls._parse_extension()
        new_cls._add_parameter_to_component(
            query_parameter=query_parameter or list(),
            header_parameter=header_parameter or list(),
            form_parameter=form_parameter or list(),
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter or list(),
            body_parameter=body_parameter,
            path_parameter=path_parameter or list(),
        )
        new_cls._add_private_key()
        new_cls._delete_response_annotation()

        return new_cls

    def copy(self) -> Self:
        """Creates a copy of this request.

        Returns
        -------
        RequestCore
            An independent request instance with copied static headers and
            query parameters.
        """
        body = copy.deepcopy(self.body) if isinstance(self.body, (*_BODY_JSON_TYPE, bytearray)) else self.body
        new_cls = self.__class__(
            self.func,
            self.method,
            self.path,
            name=self.name,
            directly_response=self.directly_response,
            headers=copy.deepcopy(self.headers),
            params=copy.deepcopy(self.params),
            body=body,
            response_parameter=self.response_parameter[:],
            **self.request_kwargs,
        )

        new_cls.header_parameter = self.header_parameter
        new_cls.query_parameter = self.query_parameter
        new_cls.path_parameter = self.path_parameter
        new_cls.body_form_parameter = self.body_form_parameter
        new_cls.body_form_encoding_type = self.body_form_encoding_type
        new_cls.body_json_parameter = self.body_json_parameter

        new_cls.body_parameter_type = self.body_parameter_type
        new_cls.body_parameter = self.body_parameter
        new_cls._body_file = self._body_file.copy() if isinstance(self._body_file, dict) else self._body_file

        new_cls._before_hook = self._before_hook
        new_cls._after_hook = self._after_hook

        new_cls._serializer = self._serializer
        new_cls._deserializer = self._deserializer
        new_cls._body_model_candidates = self._body_model_candidates
        new_cls._return_model = self._return_model
        new_cls._retry_config = self._retry_config

        new_cls.validation_parameter = self.validation_parameter

        new_cls._delete_response_annotation()
        return new_cls

    def before_hook(self, func: RequestBeforeHookT) -> RequestBeforeHookT:
        """Register a hook that runs immediately before the HTTP request.

        The hook receives ``(session, request, path)`` and must return the
        request and path to use. :class:`AsyncRequestCore` requires an async
        hook; :class:`SyncRequestCore` requires a synchronous hook.

        Parameters
        ----------
        func: Callable[..., tuple[RequestCore, str]]
            Hook to register.
        """
        self._before_hook = func
        return func

    def after_hook(self, func: RequestAfterHookT) -> RequestAfterHookT:
        """Register a hook that runs after the HTTP response is received.

        The hook receives ``(session, response)`` and may return a transformed
        result. :class:`AsyncRequestCore` requires an async hook;
        :class:`SyncRequestCore` requires a synchronous hook.

        Parameters
        ----------
        func: Callable[..., Any]
            Hook to register.
        """
        self._after_hook = func
        return func

    @property
    def is_body(self) -> bool:
        """Returns whether the HTTP request has a body element.

        Returns
        -------
        :class:`bool`
        """
        return (
            self.body_parameter is not None
            or self.is_formal_form
            or len(self.body_json_parameter) > 0
            or self.body is not None
        )

    @property
    def is_formal_form(self) -> bool:
        """Return whether this request has form parameters.

        Returns
        -------
        :class:`bool`
        """
        return len(self.body_form_parameter) > 0

    @property
    def body_type(self) -> Optional[BodyType]:
        """Return the body encoding selected for this request.

        Returns
        -------
        Optional[BodyType]
        """
        if self.body_parameter_type is not None:
            return self.body_parameter_type

        if self.body_form_encoding_type != BodyFormEncoding.AUTO:
            return self.body_form_encoding_type.body_type

        if isinstance(self.body, _BODY_JSON_TYPE):
            return BodyType.JSON
        return BodyType.RAW

    def _duplicated_check_body(self) -> None:
        """Ensure static and parameter-derived bodies are not combined.

        Raises
        ------
        TypeError
            A static body and a ``Body`` parameter were both supplied.
        """
        if self.body is not None and self.body_parameter is not None:
            raise TypeError("Only one Body Parameter or Body is allowed.")

    def _duplicated_check_body_parameter(self, single_parameter: bool = False) -> None:
        """Ensure mutually exclusive body parameter styles are not combined.

        Raises
        ------
        TypeError
            More than one of ``Body``, ``BodyJson``, and ``BodyForm`` was
            configured where only one is allowed.
        """
        if single_parameter and self.body_parameter is not None:
            raise TypeError("Duplicated Form Parameter or Body Parameter.")

        if (
            not single_parameter
            and sum(
                [
                    self.body_parameter is not None,
                    len(self.body_form_parameter) > 0,
                    len(self.body_json_parameter) > 0,
                ]
            )
            > 1
        ):
            raise TypeError("Duplicated Body Form Parameter, Body Json Parameter or Body Parameter.")

    # Setup
    def _parse_extension(self) -> None:
        if not hasattr(self.func, "__extension__"):
            return
        extension = self.func.__extension__

        # Serializer
        if "serializer" in extension.keys():
            self._serializer = extension["serializer"]
        if "deserializer" in extension.keys():
            self._deserializer = extension["deserializer"]
        if "retry" in extension.keys():
            self._retry_config = extension["retry"]

    def _bind_serializer(self, serializer: Optional[BaseCodec]) -> bool:
        """Resolve and attach a serializer using the stored body annotation.

        Returns whether a concrete serializer was found. An absent serializer
        is optional during automatic body inference, while a late-bound
        serializer must resolve successfully.
        """
        resolved_serializer: Optional[BaseSerializer]

        if serializer is not None and not serializer.is_late_bind:
            resolved_serializer = cast(BaseSerializer, serializer)
        else:
            resolved_serializer = None
            for model_candidate in self._body_model_candidates:
                if serializer is None:
                    candidate = BaseSerializer.from_model(model_candidate)
                else:
                    candidate = BaseSerializer.set_model(
                        model_candidate,
                        serializer,
                    )
                if candidate is not None:
                    resolved_serializer = candidate
                    break

        if resolved_serializer is None:
            if serializer is not None:
                raise TypeError(f"Unknown serializer type. Please check body type of " f"{self.func.__name__} method.")
            self._serializer = None
            return False

        self._serializer = resolved_serializer
        self.body_parameter_type = resolved_serializer.body_type
        return True

    def _bind_deserializer(
        self,
        deserializer: Optional[BaseCodec],
        *,
        required: bool = True,
    ) -> bool:
        """Resolve and attach a deserializer using the stored return model."""
        resolved_deserializer: Optional[BaseDeserializer]

        if deserializer is not None and not deserializer.is_late_bind:
            resolved_deserializer = cast(BaseDeserializer, deserializer)
        elif self._return_model is inspect.Signature.empty:
            resolved_deserializer = None
        elif deserializer is None:
            resolved_deserializer = BaseDeserializer.from_model(self._return_model)
        else:
            resolved_deserializer = BaseDeserializer.set_model(
                self._return_model,
                deserializer,
            )

        if resolved_deserializer is None:
            if required:
                raise TypeError(
                    f"Unknown deserializer type. Please check return annotation " f"of {self.func.__name__} method."
                )
            self._deserializer = None
            return False

        self._deserializer = resolved_deserializer
        return True

    def _bind_retry(self, config: RetryConfig) -> None:
        """Attach a retry configuration to this request."""
        self._retry_config = config

    def _add_private_key(self) -> None:
        """Add static headers and query values declared by decorators.

        This is called while the request descriptor is initialized.
        """
        self.headers.update(getattr(self.func, Header.DEFAULT_KEY, dict()))
        self.params.update(getattr(self.func, Query.DEFAULT_KEY, dict()))

    @staticmethod
    def _get_component_name(
        name: str,
        component_type: Optional[Component] = None,
    ) -> str:
        if component_type is not None and component_type.component_name is not None:
            component_name = component_type.component_name(name)
            return component_name or name
        return name

    def _add_parameter_to_component(
        self,
        *,
        query_parameter: Optional[list[str]] = None,
        header_parameter: Optional[list[str]] = None,
        body_json_parameter: Optional[list[str]] = None,
        form_parameter: Optional[list[str]] = None,
        form_encoding: Optional[BodyFormEncoding] = None,
        body_parameter: Optional[str] = None,
        path_parameter: Optional[list[str]] = None,
    ) -> None:
        """Classify decorated function parameters as request components.

        Annotations using component classes or instances take precedence;
        explicit parameter-name lists provide the legacy alternative. This is
        called while the request descriptor is initialized.

        Parameters
        ----------
        header_parameter: list[str]
            Parameter names used as headers.
        query_parameter: list[str]
            Parameter names used as query parameters.
        form_parameter: list[str]
            Parameter names used in a form body.
        body_json_parameter: list[str]
            Parameter names used in a JSON body.
        path_parameter: list[str]
            Parameter names substituted into the path.
        body_parameter: str
            Parameter name used as the complete body.
        """
        form_encoding = self.body_form_encoding_type = form_encoding or BodyFormEncoding.AUTO

        try:
            resolved_hints = get_type_hints(self.func, include_extras=True)
        except NotImplementedError:
            # Component factories such as ``Body.to_pascal()`` deliberately
            # reject unsupported declarations.  Do not hide that contract
            # when postponed annotations are evaluated here.
            raise
        except Exception:
            resolved_hints = {}

        for parameter in self._signature.parameters.values():
            annotation = resolved_hints.get(parameter.name, parameter.annotation)
            origin_type = annotation.__origin__ if is_annotated_parameter(annotation) else annotation
            metadata = annotation.__metadata__ if is_annotated_parameter(annotation) else annotation
            separated_origin = separate_union_type(origin_type)
            separated_annotation = separate_union_type(metadata)
            model_candidates = make_collection(separated_origin)

            component_type: type[Component] | type[_EmptyComponent] | type[Response] = _EmptyComponent
            component_instance: Optional[Component] = None
            for annotation in make_collection(separated_annotation):
                if isinstance(annotation, Component):
                    component_instance = annotation
                    component_type = type(annotation)
                    break

                # Generic Alias // ex.) dict[Any], list[Any], type[Any] ... etc
                if not isinstance(annotation, type):
                    continue

                if issubclass(annotation, Component) or issubclass(annotation, Response):
                    component_type = annotation
                    break

            instance_origin = [get_origin_for_generic(t) for t in model_candidates]

            if issubclass(component_type, Header) or (
                header_parameter is not None and parameter.name in header_parameter
            ):
                name = self._get_component_name(parameter.name, component_instance)
                self.header_parameter[name] = parameter
            elif issubclass(component_type, Query) or (
                query_parameter is not None and parameter.name in query_parameter
            ):
                name = self._get_component_name(parameter.name, component_instance)
                self.query_parameter[name] = parameter
            elif issubclass(component_type, Path) or (path_parameter is not None and parameter.name in path_parameter):
                self.path_parameter[parameter.name] = parameter
            elif issubclass(component_type, BodyForm) or (
                form_parameter is not None and parameter.name in form_parameter
            ):
                name = self._get_component_name(parameter.name, component_instance)
                is_file_type = is_subclass_safe(instance_origin, _IO_TYPE) or getattr(
                    component_instance, "is_file_type", False
                )
                form_component = component_instance if isinstance(component_instance, BodyForm) else None

                if form_encoding != BodyFormEncoding.AUTO:
                    self.body_parameter_type = form_encoding.body_type
                elif form_encoding == BodyFormEncoding.AUTO and is_file_type:
                    self.body_parameter_type = BodyType.FORM_DATA
                elif form_encoding == BodyFormEncoding.AUTO and self.body_parameter_type is None:
                    self.body_parameter_type = BodyType.URL_ENCODED

                self.body_form_parameter[name] = BodyFormEntry(parameter, is_file_type, form_component)
                self._duplicated_check_body_parameter()
                self._duplicated_check_body()
            elif issubclass(component_type, BodyJson) or (
                body_json_parameter is not None and parameter.name in body_json_parameter
            ):
                self.body_parameter_type = BodyType.JSON
                name = self._get_component_name(parameter.name, component_instance)
                key = getattr(component_instance, "json_key", None)

                self.body_json_parameter[name] = BodyJsonEntry(parameter, key)
                self._duplicated_check_body_parameter()
                self._duplicated_check_body()
            elif issubclass(component_type, Body) or parameter.name == body_parameter:
                self._duplicated_check_body_parameter(True)
                body_component = component_instance if isinstance(component_instance, Body) else None
                is_file_type = is_subclass_safe(instance_origin, _IO_TYPE)
                self.body_parameter = BodyEntry(parameter, is_file_type, body_component)
                if is_subclass_safe(instance_origin, _BODY_JSON_TYPE):
                    self.body_parameter_type = BodyType.JSON
                else:
                    self.body_parameter_type = BodyType.RAW

                self._body_model_candidates = tuple(model_candidates)
                self._bind_serializer(self._serializer)

                self._duplicated_check_body_parameter()
                self._duplicated_check_body()
            elif issubclass(component_type, Response) or is_subclass_safe(instance_origin, Response):
                self.response_parameter.append(parameter.name)

        # Auto set directly_response field.
        return_annotation = resolved_hints.get(
            "return",
            self._signature.return_annotation,
        )
        self._return_model = return_annotation

        # A boolean directly_response value enables automatic mode selection.
        if isinstance(self.directly_response, bool) and self.directly_response:
            if self._deserializer is not None:
                # CASE-1: deserializer defined.
                # @request()
                # @deserializer()
                # def request_method(...):
                #   pass
                self._bind_deserializer(self._deserializer)
                self.directly_response = DirectResponseType.DESERIALIZED
            # elif isinstance(return_annotation, type) and issubclass(return_annotation, Response):
            else:
                # CASE-2: deserializer not defined, but return annotation defined.
                # @request(directly_response=True)
                # def request_method(...) -> Model:
                #   pass
                if self._bind_deserializer(None, required=False):
                    self.directly_response = DirectResponseType.DESERIALIZED
                else:
                    # CASE-3(default): deserializer, return annotation not defined.
                    # @request(directly_response=True)
                    # def request_method1(...):
                    #   pass
                    #
                    # @request(directly_response=True)
                    # def request_method2(...) -> Response:
                    #   pass
                    self.directly_response = DirectResponseType.RESPONSE
        elif isinstance(self.directly_response, bool) and not self.directly_response:
            self.directly_response = DirectResponseType.NONE
        elif self.directly_response == DirectResponseType.DESERIALIZED:
            self._bind_deserializer(self._deserializer)

    def _delete_response_annotation(self) -> None:
        """Remove response parameters from the public request signature.

        Response parameters are filled automatically after the backend request
        completes and before the decorated function is executed.

        This is called while the request descriptor is initialized.
        """
        parameter_without_return_annotation = []
        for parameter in self._signature.parameters.values():
            if parameter.name in self.response_parameter:
                continue

            parameter_without_return_annotation.append(parameter)

        self._signature = self._signature.replace(parameters=parameter_without_return_annotation)
        for parameter_name in self.response_parameter:
            if parameter_name not in self.func.__annotations__.keys():
                continue

            del self.func.__annotations__[parameter_name]
        self.__annotations__ = self.func.__annotations__

    def _fill_parameter(
        self,
        session: BaseSession,
        bounded_argument: dict[str, Any] | inspect.BoundArguments,
    ) -> None:
        """Fill request components from arguments bound to the request call.

        Parameters
        ----------
        bounded_argument: dict[str, Any] | inspect.BoundArguments
            Arguments bound to the decorated request function.
        """
        if isinstance(bounded_argument, inspect.BoundArguments):
            bounded_argument = bounded_argument.arguments

        # Validation
        for _name, _parameter in bounded_argument.items():
            if _name in self.validation_parameter.keys():
                value = bounded_argument[_name]
                for func in self.validation_parameter[_name]:
                    value = func(session, value)
                bounded_argument[_name] = value

        # Header
        for _name, _parameter in self.header_parameter.items():
            # When method argument is None, it can cause an exception during the parsing process.
            if bounded_argument.get(_parameter.name) is None:
                continue
            self.headers[_name] = bounded_argument.get(_parameter.name)

        # Parameter
        for _name, _parameter in self.query_parameter.items():
            # When method argument is None, it can cause an exception during the parsing process.
            if bounded_argument.get(_parameter.name) is None:
                continue
            self.params[_name] = bounded_argument.get(_parameter.name)

        # Body
        self._duplicated_check_body()
        if self.is_formal_form and self.body_parameter is None and self.body_type == BodyType.FORM_DATA:  # self.is_body
            self.body = dict()
            self._body_file = dict()

            for _name, _entry in self.body_form_parameter.items():
                if (_entry.component is not None and _entry.component.is_file_type) or _entry.is_file_type:
                    file_name = getattr(_entry.component, "metadata_filename", None)
                    content_type = getattr(_entry.component, "metadata_content_type", None)
                    self._body_file[_name] = (
                        file_name or _name,
                        bounded_argument.get(_entry.parameter.name),
                        content_type,
                    )
                else:
                    self.body[_name] = bounded_argument.get(_entry.parameter.name)

            if len(self.body.keys()) == 0:
                self.body = None
            if len(self._body_file.keys()) == 0:
                self._body_file = None
        elif (
            self.is_formal_form and self.body_parameter is None and self.body_type == BodyType.URL_ENCODED
        ):  # self.is_body
            self.body = {
                _name: bounded_argument.get(_form_entry.parameter.name)
                for _name, _form_entry in self.body_form_parameter.items()
            }
            if len(self.body.keys()) == 0:
                self.body = None
        elif len(self.body_json_parameter) > 0 and self.body_parameter is None:
            self.body = dict()
            for _name, _json_entry in self.body_json_parameter.items():
                if _json_entry.custom_key is not None:
                    parts = _json_entry.custom_key.split(".")
                    direction = self.body
                    for part in parts[:-1]:
                        direction = direction.setdefault(part, dict())
                    direction[parts[-1]] = bounded_argument.get(_json_entry.parameter.name)
                    continue
                self.body[_name] = bounded_argument.get(_json_entry.parameter.name)
            if len(self.body.keys()) == 0:
                self.body = None
        elif self.body_parameter is not None:
            value = bounded_argument.get(self.body_parameter.parameter.name)
            body_component = self.body_parameter.component

            if self._serializer is not None:
                value = self._serializer.serialize(value)

            self.body = value
            if body_component is not None:
                if body_component.metadata_content_type is not None and not any(
                    key.lower() == "content-type" for key in self.headers
                ):
                    self.headers["Content-Type"] = body_component.metadata_content_type
                if body_component.metadata_filename is not None and not any(
                    key.lower() == "content-disposition" for key in self.headers
                ):
                    filename = body_component.metadata_filename.replace("\\", "\\\\").replace('"', '\\"')
                    self.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    def _get_request_path(self, bounded_argument: dict[str, Any] | inspect.BoundArguments) -> str:
        """Build the final request path from bound path parameters.

        Parameters
        ----------
        bounded_argument: dict[str, Any] | inspect.BoundArguments
            Arguments bound to the decorated request function.
        """
        if isinstance(bounded_argument, inspect.BoundArguments):
            bounded_argument = bounded_argument.arguments

        formatted_argument = dict()
        for _name, _parameter in self.path_parameter.items():
            value = bounded_argument.get(_parameter.name)
            formatted_argument[_name] = quote(value, safe="") if isinstance(value, str) else value
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
            and other._body_file == self._body_file
            and other.directly_response == self.directly_response
            and other.header_parameter == self.header_parameter
            and other.query_parameter == self.query_parameter
            and other.path_parameter == self.path_parameter
            and other.body_form_parameter == self.body_form_parameter
            and other.body_form_encoding_type == self.body_form_encoding_type
            and other.body_json_parameter == self.body_json_parameter
            and other.body_parameter == self.body_parameter
            and other.body_parameter_type == self.body_parameter_type
            and other._before_hook == self._before_hook
            and other._after_hook == self._after_hook
            and other._serializer == self._serializer
            and other._deserializer == self._deserializer
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self) -> Self:
        return self.copy()

    @property
    def __request_path__(self) -> str:
        return self.path

    @property
    def __core__(self) -> Self:
        return self

    def validation(self, parameter_name: str, index: Optional[int] = None) -> ValidationDecorator:
        """Register a validator for a request function parameter.

        The validator is called with ``(session, value)`` before the request is
        built. Its return value replaces the argument used in request
        components and in the decorated function.

        Parameters
        ----------
        index
        parameter_name: str
            Name of a parameter in the decorated function signature.

        Raises
        ------
        ValueError
            If the parameter name is empty or does not exist in the request
            signature.
        """
        if not parameter_name:
            raise ValueError("Parameter name is required")
        if parameter_name not in self._signature.parameters:
            raise ValueError(f"'{parameter_name}' is not a parameter of '{self.name}'")

        def decorator(
            func: ValidationFunction[Any],
        ) -> ValidationFunction[Any]:
            if inspect.iscoroutinefunction(func):
                raise TypeError("The validator must not be a coroutine.")

            if parameter_name not in self.validation_parameter:
                self.validation_parameter[parameter_name] = []

            if index is not None:
                self.validation_parameter[parameter_name].insert(index, func)
            else:
                self.validation_parameter[parameter_name].append(func)
            return func

        return decorator

    def _get_direct_response_type(
        self,
        session_directly_response: DirectResponseType | bool,
    ) -> DirectResponseType:
        """Resolve the request and session direct-response settings.

        A request-level mode takes precedence over the session default. A
        boolean session setting preserves the legacy automatic behavior:
        return a deserialized model when a deserializer is available,
        otherwise return the response wrapper.
        """
        if self.directly_response != DirectResponseType.NONE:
            return self.directly_response

        if isinstance(session_directly_response, bool):
            if not session_directly_response:
                return DirectResponseType.NONE
            if self._deserializer is not None:
                return DirectResponseType.DESERIALIZED
            return DirectResponseType.RESPONSE

        return session_directly_response

    @abstractmethod
    def _execute(self, session: Any, *args, **kwargs) -> Any:
        pass

    @overload
    def __get__(self, instance: None, instance_type: type) -> Self: ...

    @overload
    def __get__(self, instance: BaseSession, instance_type: type) -> RequestBound: ...

    @overload
    def __get__(self, instance: object, instance_type: type) -> Self: ...

    def __get__(self, instance: object | None, instance_type: type) -> Self | RequestBound:
        if isinstance(instance, BaseSession):
            return instance._get_request_bound(self)
        return self

    def __call__(self, *args, **kwargs):
        raise TypeError("RequestCore must be accessed through a Session instance.")


class AsyncRequestCore(
    RequestCore[
        AsyncRequestBeforeHookFunction[RequestCore],
        AsyncRequestAfterHookFunction[Any],
    ]
):
    session: AsyncSession

    def before_hook(
        self, func: AsyncRequestBeforeHookFunction[RequestCore]
    ) -> AsyncRequestBeforeHookFunction[RequestCore]:
        """Register an asynchronous hook that runs before the HTTP request.

        Parameters
        ----------
        func: Callable[[AsyncSession, RequestCore, str], Awaitable[tuple[RequestCore, str]]]
            Coroutine hook to register.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The pre-invoke hook must be a coroutine.")

        return super(AsyncRequestCore, self).before_hook(func)

    def after_hook(
        self, func: AsyncRequestAfterHookFunction[HookResultT]
    ) -> AsyncRequestAfterHookFunction[HookResultT]:
        """Register an asynchronous hook that runs after the HTTP response.

        Parameters
        ----------
        func: Callable[[AsyncSession, Response], Awaitable[T]]
            Coroutine hook to register.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The post-invoke hook must be a coroutine.")

        return super(AsyncRequestCore, self).after_hook(func)

    async def _execute(self, session: AsyncSession, *args, **kwargs) -> Any:
        bound_argument = self._signature.bind(session, *args, **kwargs)
        bound_argument.apply_defaults()

        req_obj: RequestCore = self.copy()

        req_obj._fill_parameter(session, bound_argument)
        formatted_path = req_obj._get_request_path(bound_argument)

        if self._before_hook is not None:
            req_obj, formatted_path = await self._before_hook(session, req_obj, formatted_path)

        def make_request_func():
            return session._make_request(req_obj, formatted_path)

        if self._retry_config is not None:
            raw_response, response = await self._retry_config.execute_async(make_request_func)
        else:
            raw_response, response = await make_request_func()

        should_close_raw_response = True
        try:
            if self._after_hook is not None:
                response = await self._after_hook(session, response)

            # Detect directly response
            direct_response_type = self._get_direct_response_type(session.directly_response)
            if direct_response_type == DirectResponseType.DESERIALIZED:
                if self._deserializer is None:
                    raise TypeError(
                        f"Unknown deserializer type. Please check return annotation of {self.func.__name__} method."
                    )
                data = self._deserializer.get_data(response) if isinstance(response, Response) else response
                return self._deserializer.deserialize(data)
            elif direct_response_type == DirectResponseType.RESPONSE:
                should_close_raw_response = response is not raw_response
                return response

            for _parameter in self.response_parameter:
                kwargs[_parameter] = response
            kwargs.update(bound_argument.arguments)

            result = await self.func(**kwargs)
        finally:
            if should_close_raw_response and not raw_response.closed:
                await raw_response.async_close()
        return result


class SyncRequestCore(
    RequestCore[
        SyncRequestBeforeHookFunction[RequestCore],
        SyncRequestAfterHookFunction[Any],
    ]
):
    session: Session

    def before_hook(
        self, func: SyncRequestBeforeHookFunction[RequestCore]
    ) -> SyncRequestBeforeHookFunction[RequestCore]:
        """Register a synchronous hook that runs before the HTTP request.

        Parameters
        ----------
        func: Callable[[Session, RequestCore, str], tuple[RequestCore, str]]
            Synchronous hook to register.
        """
        if inspect.iscoroutinefunction(func):
            raise TypeError("The pre-invoke hook must not be a coroutine.")

        return super(SyncRequestCore, self).before_hook(func)

    def after_hook(self, func: SyncRequestAfterHookFunction[HookResultT]) -> SyncRequestAfterHookFunction[HookResultT]:
        """Register a synchronous hook that runs after the HTTP response.

        Parameters
        ----------
        func: Callable[[Session, Response], T]
            Synchronous hook to register.
        """
        if inspect.iscoroutinefunction(func):
            raise TypeError("The post-invoke hook must not be a coroutine.")

        return super(SyncRequestCore, self).after_hook(func)

    def _execute(self, session: Session, *args, **kwargs) -> Any:
        bound_argument = self._signature.bind(session, *args, **kwargs)
        bound_argument.apply_defaults()

        req_obj: RequestCore = self.copy()

        req_obj._fill_parameter(session, bound_argument)
        formatted_path = req_obj._get_request_path(bound_argument)

        if self._before_hook is not None:
            req_obj, formatted_path = self._before_hook(session, req_obj, formatted_path)

        def make_request_func():
            return session._make_request(req_obj, formatted_path)

        if self._retry_config is not None:
            raw_response, response = self._retry_config.execute_sync(make_request_func)
        else:
            raw_response, response = make_request_func()

        should_close_raw_response = True
        try:
            if self._after_hook is not None:
                response = self._after_hook(session, response)

            # Detect directly response
            direct_response_type = self._get_direct_response_type(session.directly_response)
            if direct_response_type == DirectResponseType.DESERIALIZED:
                if self._deserializer is None:
                    raise TypeError(
                        f"Unknown deserializer type. Please check return annotation of {self.func.__name__} method."
                    )
                data = self._deserializer.get_data(response) if isinstance(response, Response) else response
                return self._deserializer.deserialize(data)
            elif direct_response_type == DirectResponseType.RESPONSE:
                should_close_raw_response = response is not raw_response
                return response

            for _parameter in self.response_parameter:
                kwargs[_parameter] = response
            kwargs.update(bound_argument.arguments)

            result = self.func(**kwargs)
        finally:
            if should_close_raw_response and not raw_response.closed:
                raw_response.close()
        return result


def _make_request_core(func, method, path, **kwargs):
    core_cls = AsyncRequestCore if inspect.iscoroutinefunction(func) else SyncRequestCore
    return core_cls.from_decorator(func, method, path, **kwargs)


def request(
    method: str | Method,
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    body_json_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Decorate a session method as an HTTP request.

    Accessing the decorated method on a :class:`Session` or
    :class:`AsyncSession` binds it to that session. Each invocation builds the
    request from static values and component parameters, then passes a
    :class:`Response` to matching response parameters in the decorated
    function.

    Parameters
    ----------
    name: Optional[str]
        Request name; defaults to the decorated function name.
    method: str | Method
        HTTP method.
    path: str
        Path relative to the session base URL.
    params: Optional[dict[str, Any]]
        Static query parameters.
    headers: Optional[dict[str, Any]]
        Static request headers.
    body: Optional[Any]
        Static request body.
    directly_response: DirectResponseType | bool
        Return the response after hooks without executing the decorated
        function.
    header_parameter: list[str]
        Legacy list of parameter names to use as headers.
    query_parameter: list[str]
        Legacy list of parameter names to use as query parameters.
    form_parameter: list[str]
        Legacy list of parameter names to use in a form body.
    form_encoding: Optional[BodyFormEncoding]
        Encoding to use for form parameters. ``AUTO`` selects multipart when a
        file field is present, otherwise URL encoding.
    body_json_parameter: list[str]
        Legacy list of parameter names to use in a JSON body.
    path_parameter: list[str]
        Legacy list of parameter names substituted into ``path``.
    body_parameter: str
        Legacy parameter name to use as the complete body.
    response_parameter: list[str]
        Legacy list of function parameter names that receive the response.
    **request_kwargs

    Warnings
    --------
    A complete ``Body`` parameter cannot be combined with ``BodyJson`` or
    ``BodyForm`` parameters.
    """

    def decorator(func):
        return _make_request_core(
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
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
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
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``GET`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.GET,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
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
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``POST`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.POST,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
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
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``OPTIONS`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.OPTIONS,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator


def patch(
    path: str,
    *,
    name: Optional[str] = None,
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``PATCH`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.PATCH,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
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
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``PUT`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.PUT,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
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
    directly_response: DirectResponseType | bool = False,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, Any]] = None,
    body: Optional[Any] = None,
    header_parameter: Optional[list[str]] = None,
    query_parameter: Optional[list[str]] = None,
    form_parameter: Optional[list[str]] = None,
    form_encoding: Optional[BodyFormEncoding] = None,
    body_json_parameter: Optional[list[str]] = None,
    path_parameter: Optional[list[str]] = None,
    body_parameter: Optional[str] = None,
    response_parameter: Optional[list[str]] = None,
    **request_kwargs,
) -> RequestDecorator[AsyncRequestCore, SyncRequestCore]:
    """Create a request decorator for the ``DELETE`` HTTP method.

    All parameters have the same meaning as :func:`request`.
    """

    def decorator(func):
        return _make_request_core(
            func,
            Method.DELETE,
            path,
            name=name,
            params=params,
            headers=headers,
            body=body,
            directly_response=directly_response,
            header_parameter=header_parameter,
            query_parameter=query_parameter,
            form_parameter=form_parameter,
            form_encoding=form_encoding,
            body_json_parameter=body_json_parameter,
            path_parameter=path_parameter,
            body_parameter=body_parameter,
            response_parameter=response_parameter,
            **request_kwargs,
        )

    return decorator
