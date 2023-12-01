from typing import Any


class Header:
    DEFAULT_KEY = "__DEFAULT_HEADER__"

    @staticmethod
    def default_header(key: str, value: Any):
        def decorator(func):
            if not hasattr(func, Header.DEFAULT_KEY):
                setattr(func, Header.DEFAULT_KEY, dict())
            getattr(func, Header.DEFAULT_KEY)[key] = value
            return func

        return decorator
