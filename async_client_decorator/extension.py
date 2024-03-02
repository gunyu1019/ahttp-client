from typing import Optional

from .request import RequestCore


def multiple_hook(hook: object, index: Optional[int] = -1):
    hook_name = hook.__name__
    instance = hook.__self__

    is_exist_multiple_hook = True
    if not hasattr(instance, "__multiple_%s__" % hook_name):
        is_exist_multiple_hook = False
        setattr(instance, "__multiple_%s__" % hook_name, [])

    def decorator(func):
        getattr(instance, "__multiple_%s__" % hook_name).append((func, index))
        return func

    async def wrapper(wrapped_instance, *args):
        _args = tuple(args)
        multiple_hook_func = getattr(instance, "__multiple_%s__" % hook_name)
        sorted_multiple_hook_func = sorted(multiple_hook_func, key=lambda x: x[1])
        for func, _ in sorted_multiple_hook_func:
            _args = await func(wrapped_instance, *_args)
        return _args

    if not is_exist_multiple_hook:
        hook.__func__(instance, wrapper)
    return decorator


# Pydantic Model Validate
try:
    import pydantic
except (ModuleNotFoundError, ImportError):
    is_pydantic = False
else:
    is_pydantic = True


def get_pydantic_model(model: pydantic.BaseModel):
    def decorator(func: RequestCore):
        pass

    return decorator
