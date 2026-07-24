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

from .base import BaseCodec, BaseSerializer, BaseDeserializer
from .dataclasses import DataclassesDeserializer, DataclassesSerializer

__all__ = [
    "BaseCodec",
    "BaseSerializer",
    "BaseDeserializer",
    "DataclassesSerializer",
    "DataclassesDeserializer",
]

try:
    from .pydantic import PydanticSerializer, PydanticDeserializer
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
else:
    __all__ += ["PydanticSerializer", "PydanticDeserializer"]

try:
    from .marshmallow import MarshmallowSerializer, MarshmallowDeserializer
except ModuleNotFoundError as exc:
    if exc.name != "marshmallow":
        raise
else:
    __all__ += ["MarshmallowSerializer", "MarshmallowDeserializer"]
