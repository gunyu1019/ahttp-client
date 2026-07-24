"""Discover the installed concrete backends exposed by :mod:`ahttp_client.backend`."""

from __future__ import annotations

import inspect
from collections import Counter

from ahttp_client import backend
from ahttp_client.backend import AsyncBackend, BaseBackend, SyncBackend


def _concrete_backends() -> tuple[type[BaseBackend], ...]:
    """Return each public concrete backend class once, in a stable order."""
    discovered: set[type[BaseBackend]] = set()
    for _, candidate in inspect.getmembers(backend, inspect.isclass):
        if (
            candidate in (BaseBackend, AsyncBackend, SyncBackend)
            or not issubclass(candidate, BaseBackend)
            or inspect.isabstract(candidate)
        ):
            continue
        discovered.add(candidate)
    return tuple(sorted(discovered, key=lambda candidate: candidate.__name__))


def _backend_kind(backend_type: type[BaseBackend]) -> str:
    if issubclass(backend_type, AsyncBackend):
        return "async"
    if issubclass(backend_type, SyncBackend):
        return "sync"
    raise TypeError(f"Unsupported backend type: {backend_type.__name__}")


def _backend_module(backend_type: type[BaseBackend]) -> str:
    return backend_type.__module__.rsplit(".", maxsplit=1)[-1]


def _backend_id(backend_type: type[BaseBackend], module_counts: Counter[str]) -> str:
    """Build a selector from the implementation module and its execution kind."""
    module = _backend_module(backend_type)
    if module_counts[module] == 1:
        return module
    return f"{module}_{_backend_kind(backend_type)}"


def _backend_ids(backend_types: tuple[type[BaseBackend], ...], module_counts: Counter[str]) -> tuple[str, ...]:
    ids = tuple(_backend_id(backend_type, module_counts) for backend_type in backend_types)
    id_counts = Counter(ids)
    return tuple(
        (backend_id if id_counts[backend_id] == 1 else f"{backend_id}_{backend_type.__name__.lower()}")
        for backend_type, backend_id in zip(backend_types, ids, strict=True)
    )


BACKEND_TYPES = _concrete_backends()
BACKEND_BY_SESSION = {backend_type.session_cls: backend_type for backend_type in BACKEND_TYPES}
if len(BACKEND_BY_SESSION) != len(BACKEND_TYPES):
    raise RuntimeError("Multiple backend implementations use the same session class")
_MODULE_COUNTS = Counter(_backend_module(backend_type) for backend_type in BACKEND_TYPES)

ASYNC_BACKEND_TYPES = tuple(backend_type for backend_type in BACKEND_TYPES if issubclass(backend_type, AsyncBackend))
SYNC_BACKEND_TYPES = tuple(backend_type for backend_type in BACKEND_TYPES if issubclass(backend_type, SyncBackend))
ASYNC_BACKENDS = tuple(backend_type.session_cls for backend_type in ASYNC_BACKEND_TYPES)
SYNC_BACKENDS = tuple(backend_type.session_cls for backend_type in SYNC_BACKEND_TYPES)
ASYNC_BACKEND_IDS = _backend_ids(ASYNC_BACKEND_TYPES, _MODULE_COUNTS)
SYNC_BACKEND_IDS = _backend_ids(SYNC_BACKEND_TYPES, _MODULE_COUNTS)
