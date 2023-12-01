from typing import Any


class Query:
    DEFAULT_KEY = "__DEFAULT_QUERY__"

    @staticmethod
    def default_query(key: str, value: Any):
        def decorator(func):
            if not hasattr(func, Query.DEFAULT_KEY):
                setattr(func, Query.DEFAULT_KEY, dict())
            getattr(func, Query.DEFAULT_KEY)[key] = value
            return func

        return decorator
