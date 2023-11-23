from typing import NewType

import aiohttp


class Component(NewType):
    @classmethod
    def forms(cls):
        return Body(aiohttp.FormData).__class__

    @classmethod
    def json(cls):
        return Body(dict).__class__

    @classmethod
    def body(cls, tp):
        return Body(tp).__class__

    @classmethod
    def form(cls, tp):
        return cls("form", tp).__class__

    @classmethod
    def header(cls, tp):
        return cls("header", tp).__class__

    @classmethod
    def parameter(cls, tp):
        return cls("parameter", tp).__class__


class Body(Component):
    def __init__(self, tp: type[aiohttp.FormData | dict | list]):
        if issubclass(tp, aiohttp.FormData):
            self.type = "form"
        elif issubclass(tp, (dict, list)):
            self.type = "json"
        else:
            raise TypeError("Body parameter can only have aiohttp.FormData or dict, list.")

        super().__init__("body", tp)
