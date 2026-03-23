import inspect

from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar, cast


P = ParamSpec("P")
R = TypeVar("R")


def command(
    name: str | None = None,
    description: str | None = None,
    setup_api: bool = False,
):
    def wrapper(func: Callable[P, R]) -> Callable[P, R]:
        command_func = func
        metadata_func = cast(Any, func)
        metadata_func._is_command = True
        metadata_func._command_name = name or metadata_func.__name__
        if description:
            metadata_func._command_help = description
        else:
            doc = inspect.getdoc(metadata_func)
            metadata_func._command_help = inspect.cleandoc(doc) if doc else ""

        metadata_func._command_setup_api = setup_api
        if not hasattr(metadata_func, "_command_arg_docs"):
            metadata_func._command_arg_docs = dict()

        @wraps(func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            if setup_api:
                # first arg is self
                cast(Any, args[0]).setup_api()
            return command_func(*args, **kwargs)

        return inner

    return wrapper


def annotate_arg(arg_name: str, description: str):
    def wrapper(func: Callable[P, R]) -> Callable[P, R]:
        command_func = func
        metadata_func = cast(Any, func)
        if not hasattr(metadata_func, "_command_arg_docs"):
            metadata_func._command_arg_docs = dict()

        metadata_func._command_arg_docs[arg_name] = description

        @wraps(func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            return command_func(*args, **kwargs)

        return inner

    return wrapper


def ignore_alias(func: Callable[..., Any]) -> Callable[..., Any]:
    cast(Any, func)._is_command = False
    return func
