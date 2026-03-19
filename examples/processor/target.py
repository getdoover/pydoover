import logging
from typing import Any

from pydoover.cloud.processor import ProcessorBase, run_app


class HelloWorld(ProcessorBase):
    async def setup(self):
        logging.info("Hello World Started...")

    async def on_message_create(self, event: Any):
        logging.info("Received processor event: %r", event)


def handler(event: dict[str, Any], context: Any):
    return run_app(HelloWorld(), event, context)
