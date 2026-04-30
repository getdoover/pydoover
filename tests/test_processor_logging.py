from __future__ import annotations

import contextlib
import io
import json
import logging

import pytest

from pydoover.processor._logging import (
    InvocationContextFilter,
    JsonFormatter,
    StreamToLogger,
    apply_log_levels,
    get_context,
    install_logging,
    reset_context,
    update_context,
)


@pytest.fixture(autouse=True)
def isolate_root_logger():
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    reset_context()
    try:
        yield
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)
        reset_context()


def _capture(level: int = logging.INFO) -> io.StringIO:
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(InvocationContextFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    return buf


def _records(buf: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in buf.getvalue().splitlines() if line]


def test_emits_one_json_object_per_record():
    buf = _capture()
    logging.getLogger("pydoover.test").info("hello %s", "world")

    records = _records(buf)
    assert len(records) == 1
    rec = records[0]
    assert rec["message"] == "hello world"
    assert rec["level"] == "INFO"
    assert rec["logger"] == "pydoover.test"
    # ms-since-epoch int — matches the rest of the Doover platform's
    # timestamp convention so the frontend has a single parser.
    assert isinstance(rec["timestamp"], int)
    assert rec["timestamp"] > 1_700_000_000_000  # sanity: post-2023, ms scale


def test_invocation_context_appears_as_top_level_fields():
    buf = _capture()
    update_context(lambda_request_id="abc-123", app_id="999")
    logging.getLogger("pydoover.test").info("ping")

    rec = _records(buf)[0]
    # Only ``requestId`` (the join key into the summary) and ``app_id``
    # (the lifeline for orphaned logs) ride per-record. Everything else
    # — agent_id, app_key, event_type, subscription/schedule/ingestion
    # id, organisation_id, function_name — lives on the summary and is
    # redundant given requestId-based correlation.
    assert rec["requestId"] == "abc-123"
    assert rec["app_id"] == "999"
    assert "lambda_request_id" not in rec


def test_extra_fields_on_call_site_are_preserved():
    buf = _capture()
    logging.getLogger("pydoover.test").info(
        "processed", extra={"count": 42, "duration_ms": 17}
    )

    rec = _records(buf)[0]
    assert rec["count"] == 42
    assert rec["duration_ms"] == 17


def test_exception_info_is_rendered():
    buf = _capture()
    try:
        raise ValueError("boom")
    except ValueError as e:
        logging.getLogger("pydoover.test").error("oops", exc_info=e)

    rec = _records(buf)[0]
    assert "exc_info" in rec
    assert "ValueError: boom" in rec["exc_info"]


def test_install_logging_replaces_existing_handlers():
    root = logging.getLogger()
    root.handlers = [logging.StreamHandler(io.StringIO())]
    install_logging()

    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert any(isinstance(f, InvocationContextFilter) for f in root.handlers[0].filters)


def test_install_logging_is_idempotent():
    install_logging()
    first = logging.getLogger().handlers[0]
    install_logging()
    second = logging.getLogger().handlers[0]
    # Second call must not stack a duplicate handler nor replace the
    # one we already installed.
    assert len(logging.getLogger().handlers) == 1
    assert first is second


def test_reset_context_clears_fields():
    update_context(lambda_request_id="abc", app_id="999")
    assert get_context().lambda_request_id == "abc"
    assert get_context().app_id == "999"
    reset_context()
    assert get_context().lambda_request_id is None
    assert get_context().app_id is None


def test_stream_to_logger_emits_one_record_per_line():
    buf = _capture()
    wrapper = StreamToLogger(logging.getLogger("print"), logging.INFO)

    wrapper.write("first\nsecond\n")

    records = _records(buf)
    assert [r["message"] for r in records] == ["first", "second"]
    assert all(r["logger"] == "print" and r["level"] == "INFO" for r in records)


def test_stream_to_logger_buffers_partial_writes():
    # ``print()`` issues two writes per call (the body, then the
    # terminator). Records must not appear until the newline arrives.
    buf = _capture()
    wrapper = StreamToLogger(logging.getLogger("print"), logging.INFO)

    wrapper.write("partial")
    assert _records(buf) == []
    wrapper.write(" line\n")

    rec = _records(buf)[-1]
    assert rec["message"] == "partial line"


def test_stream_to_logger_flush_emits_unterminated_buffer():
    buf = _capture()
    wrapper = StreamToLogger(logging.getLogger("print"), logging.INFO)

    wrapper.write("no newline")
    assert _records(buf) == []
    wrapper.flush()

    rec = _records(buf)[-1]
    assert rec["message"] == "no newline"


def test_redirect_stdout_routes_print_through_logger_with_context():
    # End-to-end check on the pattern run_app uses: a redirect_stdout
    # context wrapping a code block that calls ``print``. Records must
    # carry the invocation context filter's fields.
    buf = _capture()
    update_context(lambda_request_id="rid-123", app_id="999")

    with contextlib.redirect_stdout(
        StreamToLogger(logging.getLogger("print"), logging.INFO)
    ):
        print("hello from a lazy dev")

    rec = _records(buf)[-1]
    assert rec["message"] == "hello from a lazy dev"
    assert rec["level"] == "INFO"
    assert rec["logger"] == "print"
    assert rec["requestId"] == "rid-123"
    assert rec["app_id"] == "999"


def test_redirect_stderr_routes_print_through_logger_at_error_level():
    import sys

    buf = _capture()
    with contextlib.redirect_stderr(
        StreamToLogger(logging.getLogger("stderr"), logging.ERROR)
    ):
        print("kaboom", file=sys.stderr)

    rec = _records(buf)[-1]
    assert rec["message"] == "kaboom"
    assert rec["level"] == "ERROR"
    assert rec["logger"] == "stderr"


def test_install_logging_handler_binds_to_original_stdout():
    # The handler must be wired to ``sys.__stdout__`` so a later
    # ``redirect_stdout`` swap inside ``run_app`` doesn't cause its own
    # writes to re-enter the logger.
    import sys

    install_logging()
    handler = logging.getLogger().handlers[0]
    assert handler.stream is sys.__stdout__


def test_apply_log_levels_root_and_overrides():
    install_logging()
    apply_log_levels(logging.WARNING, {"pydoover.noisy": logging.ERROR})
    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger("pydoover.noisy").level == logging.ERROR
