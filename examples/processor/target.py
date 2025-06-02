import logging

from pydoover.cloud.processor import ProcessorBase


class HelloWorld(ProcessorBase):
    def setup(self): ...

    def process(self):
        logging.info("Hello World Started...")

        logging.debug("Triggerred by: %s", self.task_id)

        hello_world_channel = self.fetch_channel_named("josh-test")
        hello_world_channel.publish("Hello World1")

        logging.info("Hello World Finished")

    def close(self): ...


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    inst = HelloWorld(
        agent_id="agent_id",
        access_token="access_token",
        api_endpoint="https://my.doover.com",
        package_config={},
        msg_obj={},
        task_id="task_id",
        log_channel="log_channel",
        agent_settings={"deployment_config": {}},
    )
    inst.execute()
