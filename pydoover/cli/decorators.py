import inspect

from functools import wraps


def command(name: str = None, description: str = None, setup_api: bool = False):
    def wrapper(func):
        func._is_command = True
        func._command_name = name or func.__name__
        if description:
            func._command_help = description
        elif inspect.getdoc(func):
            func._command_help = inspect.cleandoc(inspect.getdoc(func))
        else:
            func._command_help = ""

        func._command_setup_api = setup_api
        if not hasattr(func, "_command_arg_docs"):
            func._command_arg_docs = dict()

        @wraps(func)
        def inner(*args, **kwargs):
            if setup_api:
                # first arg is self
                args[0].setup_api()
            return func(*args, **kwargs)

        return inner

    return wrapper


def annotate_arg(arg_name: str, description: str):
    def wrapper(func):
        if not hasattr(func, "_command_arg_docs"):
            func._command_arg_docs = dict()

        func._command_arg_docs[arg_name] = description

        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        return inner

    return wrapper


def ignore_alias(func):
    func._is_command = False
    return func
