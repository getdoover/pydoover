import asyncio
import json
import logging
from typing import Any

from .application import Application


def run_app(
    app: Application, event: dict[str, Any], _context, setup_logging: bool = True
):
    if setup_logging:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger().setLevel("INFO")

    # should probably fact check this but I don't think we can run asyncio.run in a lambda because it
    # recycles the environment...
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    for record in event["Records"]:
        data = json.loads(record["Sns"]["Message"])
        subscription_id = record["EventSubscriptionArn"].split(":")[-1]

        task = loop.create_task(app._handle_event(data, subscription_id))
        loop.run_until_complete(task)
