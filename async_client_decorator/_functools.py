from functools import update_wrapper, partial, WRAPPER_UPDATES

_WRAPPER_ASSIGNMENTS = (
    "__module__",
    "__name__",
    "__qualname__",
    "__doc__",
)


def update_wrap_annotations(wrapper, wrapped, annotations: dict[str, type] = None, delete_key: list[str] = None):
    __annotations__ = dict()
    annotations = annotations or dict()
    delete_key = delete_key or list()
    try:
        __annotations__ = getattr(wrapped, "__annotations__") or dict()
    except AttributeError:
        pass
    else:
        for key in delete_key:
            __annotations__.pop(key)
    finally:
        __annotations__.update(annotations)
        setattr(wrapper, "__annotations__", __annotations__)
    return wrapper


def wraps(wrapped, assigned=_WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES):
    return partial(update_wrapper, wrapped=wrapped, assigned=assigned, updated=updated)


def wrap_annotations(wrapped, annotations: dict[str, type] = None, delete_key: list[str] = None):
    return partial(update_wrap_annotations, wrapped=wrapped, annotations=annotations, delete_key=delete_key)
