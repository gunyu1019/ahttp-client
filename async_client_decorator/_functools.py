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

from functools import update_wrapper, partial, WRAPPER_UPDATES

_WRAPPER_ASSIGNMENTS = (
    "__module__",
    "__name__",
    "__qualname__",
    "__doc__",
)


def update_wrap_annotations(
    wrapper, wrapped, annotations: dict[str, type] = None, delete_key: list[str] = None
):
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


def wrap_annotations(
    wrapped, annotations: dict[str, type] = None, delete_key: list[str] = None
):
    return partial(
        update_wrap_annotations,
        wrapped=wrapped,
        annotations=annotations,
        delete_key=delete_key,
    )
