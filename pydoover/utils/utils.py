import asyncio
import json
import logging

from collections.abc import MutableMapping

from functools import wraps
from typing import Any

log = logging.getLogger(__name__)


def map_reading(in_val, output_values, raw_readings=[4, 20], ignore_below=3):
    """Map a reading to a value in a range"""
    if in_val < ignore_below:
        return None

    ## Choose the value set to map between
    lower_val_ind = 0
    found = False
    for i in range(0, len(raw_readings)):
        if in_val <= raw_readings[i]:
            lower_val_ind = i - 1
            found = True
            break

    if not found:
        lower_val_ind = len(raw_readings) - 2

    # Figure out how 'wide' each range is
    inSpan = raw_readings[lower_val_ind + 1] - raw_readings[lower_val_ind]
    outSpan = output_values[lower_val_ind + 1] - output_values[lower_val_ind]

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(in_val - raw_readings[lower_val_ind]) / float(inSpan)

    # Convert the 0-1 range into a value in the right range.
    return output_values[lower_val_ind] + (valueScaled * outSpan)


def find_object_with_key(obj: dict[Any, Any], key_to_find: str) -> Any | None:
    """Iteratively searches through a dictionary (JSON object) and returns the value for the specified key.

    Parameters
    ----------
    obj : dict
        The JSON object (dictionary) to search through.
    key_to_find : str
        The key to search for.

    Returns
    -------
    Any
        The object containing the key, or None if the key is not found.
    """
    stack = [obj]

    while stack:
        current = stack.pop()

        if isinstance(current, dict):
            if key_to_find in current:
                return current[key_to_find]

            for key in current:
                stack.append(current[key])

    return None


def find_path_to_key(obj: dict[Any, Any], key_to_find: str) -> str | None:
    """Iteratively searches through a dictionary (JSON object) and returns the path to the specified key.

    Parameters
    ----------
    obj : dict
        The JSON object (dictionary) to search through.
    key_to_find : str
        The key to search for.

    Returns
    -------
    str, optional
        The path to the key, or None if the key is not found.

    """

    stack = [{"current": obj, "path": ""}]

    while stack:
        current_entry = stack.pop()
        current = current_entry["current"]
        path = current_entry["path"]

        if isinstance(current, dict):
            if key_to_find in current:
                return f"{path}.{key_to_find}" if path else key_to_find

            for key in current:
                new_path = f"{path}.{key}" if path else key
                stack.append({"current": current[key], "path": new_path})

    return None


def get_is_async(is_async: bool = None):
    if is_async is not None:
        return is_async

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True


def maybe_async():
    """Wrapper to allow both a sync and async variation on the same function to provide a unified interface to the user.

    This is useful when writing library functions for both a sync and async context.

    It assumes you have a variation of your function with the same signature suffixed with `_async`.

    Examples
    --------

    A simple example::

        class MyClass:
            @maybe_async()
            def my_function(self, value: str):
                print("This is the sync version of my_function")
                return "sync result"

            async def my_function_async(self, value: str):
                print("This is the async version of my_function")
                return "async result"



    If the user was running an asynchronous main loop, `my_function` would be invoked as follows::

        class MyApp(Application):
            async def main_loop(self):
                result = await obj.my_function("test")
                print(result)  # This would print "async result"


    However, if the main loop was synchronous, it would invoke the sync version of the function::

        class MyApp(Application):
            def main_loop(self):
                result = self.my_function("test")
                print(result)  # This would print "sync result"

    """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # args[0] is self
            is_async_context = getattr(args[0], "_is_async", False)
            # allow them to specify if they want to run the sync version of the function (default very much not)
            force_sync = kwargs.pop("run_sync", False)

            if is_async_context is True and force_sync is False:
                # we're in an async context, check if we have an async variety of the function to run...
                try:
                    alternative = getattr(args[0], f"{func.__name__}_async")
                    return alternative(*args[1:], **kwargs)
                except AttributeError:
                    # we don't have a corresponding async method, just use the sync one.
                    pass
            return func(*args, **kwargs)

        return inner

    return wrapper


def wrap_try_except(func, *args, **kwargs):
    """Wrapper function to catch exceptions and log them. This does not propagate the exception."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log.exception(f"Error in {func.__name__}: {e}", exc_info=e)


async def wrap_try_except_async(func, *args, **kwargs):
    """Wrapper function to catch exceptions in an async function and log them. This does not propagate the exception."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        log.exception(f"Error in {func.__name__}: {e}", exc_info=e)


async def call_maybe_async(
    func, *args, as_task: bool = False, in_executor: bool = True, **kwargs
):
    """Helper function to call a function that may be either synchronous or asynchronous.

    Parameters
    ----------
    func : callable
        The function to call, which may be synchronous or asynchronous.

    *args
        Arguments to pass to the function.

    as_task : bool
        If True, the function will be called as an asyncio task. Default is False.

    in_executor : bool
        If True, the function will be run in an executor if it is not a coroutine function. Default is True.

    **kwargs
        Any kwargs to pass to the function.
    """
    # print(f"call_maybe_async: func={func}, as_task={as_task}, in_executor={in_executor is True and not asyncio.iscoroutinefunction(func)}")
    if asyncio.iscoroutinefunction(func):
        # coro = wrap_try_except_async(func, *args, **kwargs)
        coro = func(*args, **kwargs)
        if as_task:
            # assign it to a variable for weak ref
            task = asyncio.create_task(coro)
            return task
        else:
            return await coro
    elif in_executor:
        loop = asyncio.get_running_loop()
        # run_in_executor doesn't support kwargs
        if kwargs:
            log.warning("kwargs are not supported when calling via executor")

        # this is a little bit of a hack, but essentially we're creating an async function that
        # is called with await func to allow for both running as a task and in an executor.
        # future = loop.run_in_executor(None, wrap_try_except, func, *args)
        future = loop.run_in_executor(None, func, *args, **kwargs)
        if as_task:
            return future

        return await future
    else:
        # return wrap_try_except(func, catch_exception, *args, **kwargs)
        return func(*args, **kwargs)


def on_change(callback, name=None):
    """A decorator that triggers a callback when the output of the decorated function changes.

    The callback is called with four arguments:
      - new_result: The new output of the function.
      - old_result: The previous output (or None if this is the first call).
      - is_first: A boolean indicating if this is the first time the function has returned a value.
      - change_detector_name: The optional name identifying this change detector.

    :param callback: The callback function to trigger, or a string indicating the name of an instance attribute.
    :param name: An optional name for this change_detector_name.

    Examples
    ---------

    A simple usage example::


        class MyClass:
            def __init__(self):
                self.last = None

            def my_callback(self, new_result, old_result, is_first, change_detector_name):
                if is_first:
                    print(f"{change_detector_name} has returned a value for the first time: {new_result}")
                else:
                    print(f"{change_detector_name} has changed from {old_result} to {new_result}")

            @on_change("my_callback", name="my_function")
            def my_function(self):
                import random
                return random.randint(0, 100)

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            detector_name = name or func.__name__

            # Check if we're dealing with an instance method.
            if args and hasattr(args[0], "__dict__"):
                instance = args[0]
                state_attr = f"__on_change_state_{detector_name}"
                # Retrieve state from the instance, or initialize it if not present.
                state = getattr(
                    instance, state_attr, {"last_result": None, "has_value": False}
                )
            else:
                # For non-instance functions, fallback to closure state.
                # (You could also raise an error if you only expect instance methods.)
                state = wrapper.__dict__.setdefault(
                    "state", {"last_result": None, "has_value": False}
                )

            result = func(*args, **kwargs)
            is_first = not state["has_value"]

            # Trigger the callback if it's the first call or if the result has changed.
            if is_first or result != state["last_result"]:
                # Determine which callback to use.
                if isinstance(callback, str):
                    if not args:
                        raise ValueError(
                            "Expected a 'self' argument when using a string callback."
                        )
                    cb = getattr(args[0], callback, None)
                    if cb is None or not callable(cb):
                        raise ValueError(
                            f"Attribute '{callback}' is not a callable of the instance."
                        )
                else:
                    cb = callback

                cb(
                    result,
                    state["last_result"] if state["has_value"] else None,
                    is_first,
                    detector_name,
                )
                state["last_result"] = result
                state["has_value"] = True

                # Save the updated state back to the instance (or closure, as applicable).
                if args and hasattr(args[0], "__dict__"):
                    setattr(instance, state_attr, state)
                else:
                    wrapper.__dict__["state"] = state

            return result

        return wrapper

    return decorator


class CaseInsensitiveDict(MutableMapping):
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def copy(self):
        return CaseInsensitiveDict(self._store)

    def to_dict(self):
        return {
            k: v.to_dict() if isinstance(v, CaseInsensitiveDict) else v
            for k, v in self.items()
        }

    @classmethod
    def from_dict(cls, data):
        t = {
            k: CaseInsensitiveDict.from_dict(v) if isinstance(v, dict) else v
            for k, v in data.items()
        }
        return cls(t)

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return iter(self._store)

    def __setitem__(self, key, value):
        self._store[key.lower()] = value

    def __getitem__(self, key):
        return self._store[key.lower()]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._store)


class CaseInsensitiveDictEncoder(json.JSONEncoder):
    # might not need this
    def default(self, obj):
        if isinstance(obj, CaseInsensitiveDict):
            return obj.to_dict()
        # Let the base class default method raise the TypeError
        return super().default(obj)


class LogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(debug: bool):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(LogFormatter())
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)
