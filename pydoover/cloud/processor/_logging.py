"""Structured logging plumbing for processor invocations.

Two responsibilities:

1. Install a stdout handler that emits each :class:`logging.LogRecord`
   as a single JSON line. Lambda's S3 log delivery wraps each line as a
   string in the envelope's ``message`` field — that's by design and
   matches how AWS Powertools logs land too — but the inner blob is
   well-formed JSON, so downstream consumers ``serde_json::from_str``
   the ``message`` to recover structure.
2. Stamp ``requestId`` and ``app_id`` onto every record via a
   :class:`logging.Filter` that reads from a module-level singleton.
   These are the only two fields the log filter needs — every other
   per-invocation field (event_type, subscription_id, agent_id, etc.)
   lives on the ``Application`` instance and gets copied into the
   summary message at the end of the invocation.

Lambda is single-threaded per invocation, so the singleton is safe and
just gets reset at the start of each event.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class InvocationContext:
    lambda_request_id: str | None = None
    app_id: str | None = None

    def as_log_fields(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.lambda_request_id is not None:
            out["requestId"] = self.lambda_request_id
        if self.app_id is not None:
            out["app_id"] = self.app_id
        return out


_current: InvocationContext = InvocationContext()


def reset_context() -> InvocationContext:
    global _current
    _current = InvocationContext()
    return _current


def get_context() -> InvocationContext:
    return _current


def update_context(**kwargs: Any) -> None:
    for k, v in kwargs.items():
        setattr(_current, k, v)


# Standard ``LogRecord`` attributes — anything not in this set is treated
# as user-supplied extra context and serialised as a top-level field.
_STD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Render each :class:`LogRecord` as a single JSON line.

    Produces ``{timestamp, level, logger, message, ...extras}`` where
    extras are any attributes set on the record (via ``extra=`` or by a
    filter). Exceptions are serialised under ``exc_info`` as the
    rendered traceback string.
    """

    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "timestamp": int(record.created * 1000),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _STD_ATTRS or key in out:
                continue
            out[key] = value
        if record.exc_info:
            out["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            out["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(out, default=str)


class InvocationContextFilter(logging.Filter):
    """Inject the current invocation context onto each LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in _current.as_log_fields().items():
            if not hasattr(record, k):
                setattr(record, k, v)
        return True


class StreamToLogger:
    """File-like object that routes writes through the logging system.

    Used with :func:`contextlib.redirect_stdout` / ``redirect_stderr``
    in :func:`run_app` so stray ``print`` calls from app code come out
    as proper JSON log records (with ``requestId`` / ``app_id`` from
    the filter) instead of as raw text that bypasses the formatter.

    The handler installed by :func:`install_logging` is bound to
    ``sys.__stdout__`` — Python's reference to the original fd-1
    stream — so its writes don't re-enter this wrapper.
    """

    def __init__(self, logger: logging.Logger, level: int):
        self._logger = logger
        self._level = level
        self._buffer = ""

    def write(self, msg: str) -> int:
        # ``print()`` issues two writes per call (the body, then the
        # terminator), so buffer until we see a newline.
        self._buffer += msg
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line:
                self._logger.log(self._level, line)
        return len(msg)

    def flush(self) -> None:
        if self._buffer:
            self._logger.log(self._level, self._buffer)
            self._buffer = ""

    def isatty(self) -> bool:
        return False


def install_logging(default_level: int = logging.INFO) -> None:
    """Configure the root logger to emit JSON to stdout.

    Replaces any pre-existing handlers — Lambda's runtime may have
    installed one with its own formatter, and we want a deterministic
    structured shape (with millisecond timestamps and a controlled
    field set) regardless. Lambda's S3 delivery will still wrap each
    line as a string in the envelope's ``message`` field; that's
    unavoidable from the producer side and matches AWS Powertools.

    Idempotent: safe to call once per cold start AND on every warm
    invocation (the second call is effectively a no-op).

    Note: capturing ``print`` / ``sys.stderr`` writes is the
    responsibility of :func:`run_app`, which scopes a
    :class:`StreamToLogger` redirect to the invocation. Keeping the
    redirect out of here preserves the separation between "configure
    logging" and "scope an invocation."
    """
    # Bind to ``__stdout__`` so ``run_app``'s ``redirect_stdout`` swap
    # doesn't cause this handler's own writes to loop back through the
    # logger.
    handler = logging.StreamHandler(sys.__stdout__)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(InvocationContextFilter())

    root = logging.getLogger()
    if not any(_is_pydoover_handler(h) for h in root.handlers):
        root.handlers = [handler]
    root.setLevel(default_level)


def _is_pydoover_handler(handler: logging.Handler) -> bool:
    return isinstance(handler.formatter, JsonFormatter)


def apply_log_levels(
    level: str | int | None,
    overrides: dict[str, str | int] | None,
) -> None:
    if level is not None:
        logging.getLogger().setLevel(level)
    if overrides:
        for name, lvl in overrides.items():
            logging.getLogger(name).setLevel(lvl)
