from typing import Any


class Form:
    DEFAULT_KEY = "__DEFAULT_Form__"

    @staticmethod
    def default_form(key: str, value: Any):
        def decorator(func):
            if not hasattr(func, Form.DEFAULT_KEY):
                setattr(func, Form.DEFAULT_KEY, dict())
            getattr(func, Form.DEFAULT_KEY)[key] = value
            return func

        return decorator
