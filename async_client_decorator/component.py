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

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Callable
    from typing_extensions import Self


class EmptyComponent:
    pass


class Component:
    get_component_name: Optional[Callable[[str], str]]

    @classmethod
    def custom_name(cls, name: str) -> type[Self]:
        cls.get_component_name = lambda _: name
        return cls

    @staticmethod
    def _to_pascal(snake: str) -> str:
        camel = snake.title()
        return re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)

    @staticmethod
    def _to_camel(snake: str) -> str:
        camel = Component._to_pascal(snake)
        return re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)

    @classmethod
    def to_camel(cls) -> type[Self]:
        cls.get_component_name = lambda original_name: Component._to_camel(original_name)
        return cls

    @classmethod
    def to_pascal(cls) -> type[Self]:
        cls.get_component_name = lambda original_name: Component._to_pascal(original_name)
        return cls
