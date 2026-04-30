import asyncio
import contextlib
import json
import logging
import os
from typing import Any

from .application import Application
from ._logging import (
    StreamToLogger,
    install_logging,
    reset_context,
    update_context,
)


# should probably fact check this but I don't think we can run asyncio.run in a lambda because it
# recycles the environment...
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()


def run_app(
    app: Application, event: dict[str, Any], context, setup_logging: bool = True
):
    if setup_logging:
        debug_env = os.environ.get("DEBUG", "FALSE").upper()
        default_level = logging.DEBUG if debug_env in ("TRUE", "1") else logging.INFO
        install_logging(default_level=default_level)

    reset_context()
    app.lambda_request_id = (
        getattr(context, "aws_request_id", None) if context else None
    )
    app.lambda_function_name = (
        getattr(context, "function_name", None) if context else None
    )
    app.lambda_function_version = (
        getattr(context, "function_version", None) if context else None
    )
    update_context(lambda_request_id=app.lambda_request_id)

    # 2 sources are valid, SNS for subscriptions, EventBridge for schedules
    # in reality anything that isn't an AWS (SNS) payload will be passed through as-is
    try:
        source = event["Records"][0]["EventSource"]
    except KeyError:
        data = event
        subscription_id = None
    else:
        if source == "aws:sns":
            data = json.loads(event["Records"][0]["Sns"]["Message"])
            subscription_id = event["Records"][0]["EventSubscriptionArn"]
        else:
            raise ValueError(
                "Unknown event. Must originate from SNS or EventBridge Schedules"
            )

    # Route stray ``print()`` / ``print(..., file=sys.stderr)`` from app
    # code through the logger for the duration of the invocation, so they
    # land in S3 as JSON records (with requestId/app_id) instead of as
    # raw text that breaks the on-disk shape.
    with (
        contextlib.redirect_stdout(
            StreamToLogger(logging.getLogger("print"), logging.INFO)
        ),
        contextlib.redirect_stderr(
            StreamToLogger(logging.getLogger("stderr"), logging.ERROR)
        ),
    ):
        task = loop.create_task(app._handle_event(data, subscription_id))
        return loop.run_until_complete(task)
