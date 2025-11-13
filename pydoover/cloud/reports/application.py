
import asyncio
from datetime import datetime, timedelta
import logging
import os
import time

from typing import Any

from ..processor.types import MessageCreateEvent, DeploymentEvent, ScheduleEvent
from ..processor.data_client import DooverData
from ...config import Schema


log = logging.getLogger()


DEFAULT_DATA_ENDPOINT = "https://data.udoover.com/api"
DEFAULT_OFFLINE_PERIOD_END = 60 * 60  # 1 hour
SPLIT_MESSAGES_LIMIT = 100  # 1 hour


class Application:
    def __init__(self, config: Schema | None):
        self.config = config

        self._api_endpoint = (
            os.environ.get("DOOVER_DATA_ENDPOINT") or DEFAULT_DATA_ENDPOINT
        )

        self.api = DooverData(self._api_endpoint)

        # set per-task
        self.agent_id: int = None
        self._initial_token: str = None
        self._tag_values: dict[str, Any] = None
        self._connection_config: dict[str, Any] = None


    async def _setup(self):
        self._publish_tags = False

        # this is ok to setup because it doesn't store any state
        await self.api.setup()

        # this is essentially an oauth2 "upgrade" request with some more niceties.
        # we give it a minimal token provisioned from doover data, along with our subscription (uuid) ID
        # and we get back a full token, agent id, app key and a few common channels - ui state, ui cmds,
        # tag values and deployment config.
        self.api.set_token(self._initial_token)

        if self.subscription_id:
            data = await self.api.fetch_processor_info(self.subscription_id)
        elif self.schedule_id:
            data = await self.api.fetch_schedule_info(self.schedule_id)
        else:
            raise ValueError("No subscription or schedule ID provided.")

        self.agent_id = self.api.agent_id = data["agent_id"]
        self.api.set_token(data["token"])

        # this should match the original organisation ID, but in case it doesn't, this should
        # probably be the source of truth
        self.api.organisation_id = data["organisation_id"]

        self.app_key = data["app_key"]

        if self.config is not None:
            # if there's no config defined this can legitimately be None in which case don't bother.
            self.config._inject_deployment_config(data["deployment_config"])

    async def _close(self):
        await self.api.close()

    async def setup(self):
        """The setup function to be invoked period_start any processing of a message.

        This is designed to be overridden by a user to perform any setup required.

        You do **not** need to call `super().setup()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def close(self):
        """Override this method to change behaviour period_start a processor exits.

        This is invoked period_end the processing of a message is complete, and can be used to clean up resources or perform any final actions.

        You do **not** need to call `super().close()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def _on_message_create(self, event: MessageCreateEvent):
        log.error("Report Genertator does not support message create events")
        pass

    async def on_deployment(self, event: DeploymentEvent):
        pass
    
    async def _on_schedule(self, event: ScheduleEvent):
        if self.config.report_config.schedule_id.value is None:
            log.error("No schedule ID provided")
            return
        
        if len(self.config.report_config.devices.elements) == 0:
            log.error("No Devices provided")
            return
        
        # Calculate the period for the schedule report
        self.config.report_config.period_end.value = end_time = datetime.now()
        
        schedule_ferquency = self.config.report_config.schedule_frequency.value
        match schedule_ferquency:
            case "Hourly":
                self.config.report_config.period_start.value = end_time - timedelta(hours=1)
            case "Daily":
                self.config.report_config.period_start.value = end_time - timedelta(days=1)
            case "Weekly":
                self.config.report_config.period_start.value = end_time - timedelta(weeks=1)
            case "Monthly":
                self.config.report_config.period_start.value = end_time - timedelta(months=1)
            case "Quarterly":
                self.config.report_config.period_start.value = end_time - timedelta(months=3)
            case "Never":
                log.error("Subscription frequency is Never")
                return
            case _:
                log.error(f"Unknown schedule frequency {schedule_ferquency}")
                return
        
        devices = [device.value for device in self.config.report_config.devices.elements]
            
        self._report_metadata = {
            "devices": devices,
            "period_start": int(self.config.report_config.period_start.value.timestamp() * 1000),
            "period_end": int(self.config.report_config.period_end.value.timestamp() * 1000),
            "schedule_id": str(self.config.report_config.schedule_id.value),
            "report_genertator": "TODO",
            "status": "Generating",
            "logs": "",
        }

        try:
            data = await self.api.publish_message(self.agent_id, "reports", self._report_metadata, organisation_id=self.agent_id)
        except Exception as e:
            log.error(f"Error creating report message: {e}")
            return
        
        if "id" not in data:
            log.error("Error creating report message: cannot find id in response")
            return
        
        self._report_metadata["id"] = data["id"]
        self._report_id = data["id"]
        self.report_id = data["id"]

        await self._generate(devices, self.config.report_config.period_start.value, self.config.report_config.period_end.value)
        
    
    async def _on_single_execute(self, event: ScheduleEvent):
        if len(self.config.report_config.devices.elements) == 0:
            log.error("No Devices provided")
            return
        
        if self.config.report_config.period_start.value is None:
            log.error("No Period Start provided")
            return
        
        if self.config.report_config.period_end.value is None:
            log.error("No Period End provided")
            return
        
        if self.config.report_config.report_id.value is None:
            log.error("No Report Id provided")
            return
        
        devices = [device.value for device in self.config.report_config.devices.elements]
        self._generate(devices, self.config.report_config.period_start.value, self.config.report_config.period_end.value)
    
    async def _generate(self, agent_ids: list[int], period_start: datetime, period_end: datetime):

        await self.generate(agent_ids, period_start, period_end)
        
    async def generate(self, agent_ids: list[int], period_start: datetime, period_end: datetime):
        """Override this method to specify how a report should be generated.

        You do **not** need to call `super().generate()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def _handle_event(self, event: dict[str, Any], subscription_id: str = None):
        start_time = time.time()
        log.info("Initialising processor task")
        log.info(f"Started at {start_time}.")

        # self.app_key: str = event.get("app_key", os.environ.get("APP_KEY"))
        # self.agent_id: int = event["agent_id"]
        self.subscription_id = subscription_id

        try:
            self.schedule_id = event["d"]["schedule_id"]
        except KeyError:
            self.schedule_id = None

        try:
            # org ID should be set in both schedules and subscriptions, but just in case it isn't...
            self.organisation_id = event["d"]["organisation_id"]
        except KeyError:
            self.organisation_id = None

        # this is the initial token provided. For a subscription, it will be a temporary token.
        # For a schedule, it will be a long-lived token.
        # Both have permission to access the info endpoint, only.
        self._initial_token = event["token"]
        # this can be set during testing. during normal operation it's signed in the JWT.
        self.agent_id = event.get("agent_id")

        s = time.perf_counter()
        await self._setup()
        log.info(f"Setup took {time.perf_counter() - s} seconds.")

        s = time.perf_counter()
        try:
            await self.setup()
        except Exception as e:
            log.error(f"Error attempting to setup processor: {e} ", exc_info=e)
        log.info(f"user Setup took {time.perf_counter() - s} seconds.")

        func = None
        payload = None
        match event["op"]:
            case "on_message_create":
                func = self._on_message_create
                payload = MessageCreateEvent.from_dict(event["d"])
                # prevent infinite loops
                self.api._invoking_channel_name = payload.channel_name
            case "on_deployment":
                func = self.on_deployment
                payload = DeploymentEvent.from_dict(event["d"])
            case "on_schedule":
                func = self._on_schedule
                payload = ScheduleEvent.from_dict(event["d"])

        if func is None:
            log.error(f"Unknown event type: {event['op']}")
        else:
            try:
                s = time.perf_counter()
                await func(payload)
                log.info(f"Processing event took {time.perf_counter() - s} seconds.")
            except Exception as e:
                log.error(f"Error attempting to process event: {e} ", exc_info=e)

        if self._publish_tags:
            await self.api.publish_message(
                self.agent_id, "tag_values", self._tag_values
            )

        try:
            await self.close()
        except Exception as e:
            log.error(f"Error attempting to close processor: {e} ", exc_info=e)

        await self._close()

        end_time = time.time()
        log.info(
            f"Finished at {end_time}. Process took {end_time - start_time} seconds."
        )

    async def fetch_device_in_window(self, agent_id: int, channel_name: str, period_start: datetime, period_end: datetime):
        """Helper method to fetch the messages from a device channel in a window.

        Parameters
        ----------
        agent_id : int
            The agent ID who owns the channel.
        channel_name : str,
            The name of the channel to fetch.
        period_start : datetime
            The start of the window.
        period_end : datetime
            The end of the window.

        Returns
        -------
        :class:`pydoover.cloud.api.Messages`
            The messages object corresponding to the given window.

        Raises
        -------
        :class:`pydoover.cloud.api.NotFound`
            If the channel with the specified key does not exist.
        """
        return await self.api.get_channel_messages(agent_id, channel_name, after=period_start, before=period_end, chunk_size=SPLIT_MESSAGES_LIMIT, organisation_id=self.agent_id)

    async def fetch_devices_in_window(self, agent_ids: list[int], channel_name: str, period_start: datetime, period_end: datetime):
        """Helper method to fetch the messages from a device channel in a window.

        Parameters
        ----------
        agent_id : int
            The agent ID who owns the channel.
        channel_name : str,
            The name of the channel to fetch.
        period_start : datetime
            The start of the window.
        period_end : datetime
            The end of the window.

        Returns
        -------
        :class:`pydoover.cloud.api.Messages`
            The messages object corresponding to the given window.

        Raises
        -------
        :class:`pydoover.cloud.api.NotFound`
            If the channel with the specified key does not exist.
        """
        
        # Start the tasks
        tasks = []
        for agent_id in agent_ids:
            tasks.append(self.fetch_device_in_window(agent_id, channel_name, period_start, period_end))
        
        # Collect the results
        results = await asyncio.gather(*tasks)
        
        # Return the results
        return {
            agent_id: result for agent_id, result in zip(agent_ids, results)
        }