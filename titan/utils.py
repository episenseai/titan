import asyncio

from pydantic import BaseModel


class ImmutBaseModel(BaseModel):
    class Config:
        # faux immutability of fields
        allow_mutation = False
        # validate field defaults
        validate_all = True


class AssignValidateBaseModel(BaseModel):
    class Config:
        # whether to perform validation on assignment to attributes
        validate_assignment = True


class StrictBaseModel(BaseModel):
    class Config:
        allow_mutation = False
        validate_all = True
        # whether to ignore, allow, or forbid extra attributes during model initialization.
        extra = "forbid"


def coro(f):
    """
    Coroutine function decorator.

    Wraps around an aync function to provide a synchoronous/normal function.
    Calling the returned **wrapper** function runs the **wrapped** async function
    using `asyncio.get_event_loop().run_until_complete(wrapped_func)` till
    comletion and returns the result.
    """
    from functools import wraps
    from inspect import iscoroutinefunction

    assert iscoroutinefunction(f), f"Expected async def func: ({f})"

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))

    return wrapper
