"""Mypy plugin for declarative ahttp_client endpoint methods.

The runtime request descriptors skip the decorated method body when
``directly_response=True``. Mypy cannot infer that behavior from a regular
decorator, so it otherwise reports ``empty-body`` for a body containing only
``...`` or ``pass``.

Enable the plugin in a mypy configuration file:

.. code-block:: ini

    [mypy]
    plugins = ahttp_client.mypy
"""

from __future__ import annotations

from typing import Callable, Final

from mypy.nodes import CallExpr, Decorator, Expression, MemberExpr, NameExpr, RefExpr, TypeInfo
from mypy.plugin import ClassDefContext, Plugin
from mypy.types import CallableType, Instance, Type, UnboundType, UnionType, get_proper_type

_SESSION_BASES: Final = frozenset(
    {
        "ahttp_client.session.AsyncSession",
        "ahttp_client.session.Session",
    }
)
_REQUEST_DECORATORS: Final = frozenset(
    {
        "ahttp_client.request.request",
        "ahttp_client.request.get",
        "ahttp_client.request.post",
        "ahttp_client.request.options",
        "ahttp_client.request.patch",
        "ahttp_client.request.put",
        "ahttp_client.request.delete",
    }
)
_TRANSPARENT_DECORATORS: Final = _REQUEST_DECORATORS | {
    "ahttp_client.retry.retry",
    "ahttp_client.serializer.serialize",
    "ahttp_client.serializer.deserialize",
}


def _request_call(expression: Expression) -> CallExpr | None:
    if not isinstance(expression, CallExpr):
        return None
    if not isinstance(expression.callee, RefExpr):
        return None
    if expression.callee.fullname not in _REQUEST_DECORATORS:
        return None
    return expression


def _decorator_fullname(expression: Expression) -> str | None:
    callee = expression.callee if isinstance(expression, CallExpr) else expression
    return callee.fullname if isinstance(callee, RefExpr) else None


def _is_explicit_direct_response(expression: Expression) -> bool:
    """Return whether an endpoint decorator statically enables direct mode."""
    call = _request_call(expression)
    if call is None:
        return False

    for name, value in zip(call.arg_names, call.args):
        if name != "directly_response":
            continue
        if isinstance(value, NameExpr):
            return value.name == "True"
        if isinstance(value, MemberExpr):
            return (
                isinstance(value.expr, RefExpr)
                and value.expr.fullname == "ahttp_client.enum.DirectResponseType"
                and value.name in {"RESPONSE", "DESERIALIZED"}
            )
        return False
    return False


def _is_response_type(annotation: Type) -> bool:
    proper = get_proper_type(annotation)
    if isinstance(proper, Instance):
        return proper.type.fullname == "ahttp_client.response.Response"
    if isinstance(proper, UnboundType):
        return proper.name in {"Response", "ahttp_client.response.Response"}
    if isinstance(proper, UnionType):
        return any(_is_response_type(item) for item in proper.items)
    return False


def _restore_endpoint_signature(statement: Decorator) -> bool:
    """Expose the original handler signature through the request descriptor."""
    original = get_proper_type(statement.func.type)
    decorated = get_proper_type(statement.var.type)
    if not isinstance(original, CallableType):
        return False

    retained = [index for index, argument_type in enumerate(original.arg_types) if not _is_response_type(argument_type)]
    if len(retained) == len(original.arg_types):
        return False
    fallback = decorated if isinstance(decorated, Instance) else original.fallback
    public_signature = original.copy_modified(
        arg_types=[original.arg_types[index] for index in retained],
        arg_kinds=[original.arg_kinds[index] for index in retained],
        arg_names=[original.arg_names[index] for index in retained],
        fallback=fallback,
    )
    statement.func.type = public_signature
    statement.var.type = public_signature
    return True


def _mark_direct_endpoint_bodies(ctx: ClassDefContext) -> None:
    """Restore endpoint types and mark direct declarations as generated."""
    for statement in ctx.cls.defs.body:
        if not isinstance(statement, Decorator):
            continue
        request_decorators = [item for item in statement.original_decorators if _request_call(item) is not None]
        if not request_decorators:
            continue

        if _restore_endpoint_signature(statement):
            statement.decorators[:] = [
                item for item in statement.decorators if _decorator_fullname(item) not in _TRANSPARENT_DECORATORS
            ]
        if not any(_is_explicit_direct_response(item) for item in request_decorators):
            continue
        symbol = ctx.cls.info.names.get(statement.name)
        if symbol is not None:
            # Mypy skips empty-body diagnostics for plugin-generated methods
            # while retaining normal signature and body type checking.
            symbol.plugin_generated = True


class AhttpClientPlugin(Plugin):
    """Teach mypy about endpoint bodies skipped by request descriptors."""

    def _is_session_base(self, fullname: str) -> bool:
        if fullname in _SESSION_BASES:
            return True
        symbol = self.lookup_fully_qualified(fullname)
        return (
            symbol is not None
            and isinstance(symbol.node, TypeInfo)
            and any(base.fullname in _SESSION_BASES for base in symbol.node.mro)
        )

    def get_base_class_hook(
        self,
        fullname: str,
    ) -> Callable[[ClassDefContext], None] | None:
        if self._is_session_base(fullname):
            return _mark_direct_endpoint_bodies
        return None


def plugin(version: str) -> type[Plugin]:
    """Return the plugin class expected by mypy."""
    return AhttpClientPlugin
