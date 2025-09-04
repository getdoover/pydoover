import asyncio
import json
import logging
from typing import Any

from .application import Application


# should probably fact check this but I don't think we can run asyncio.run in a lambda because it
# recycles the environment...
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()


def run_app(
    app: Application, event: dict[str, Any], _context, setup_logging: bool = True
):
    if setup_logging:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().setLevel("INFO")

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

    task = loop.create_task(app._handle_event(data, subscription_id))
    loop.run_until_complete(task)
