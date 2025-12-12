import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import time
import croniter

from ..processor.types import ManualInvokeEvent, MessageCreateEvent, DeploymentEvent, ScheduleEvent
from ..processor.application import Application as ApplicationBase
from ...config import Schema


log = logging.getLogger()

SPLIT_MESSAGES_LIMIT = 100  # 1 hour


class Application(ApplicationBase):
    def __init__(self, config: Schema | None):
        super().__init__(config)

        self.period_start = None
        self.period_end = None
        self.devices = None
        
    async def on_message_create(self, event: MessageCreateEvent):
        log.error("Report Genertator does not support message create events")
        pass

    async def on_deployment(self, event: DeploymentEvent):
        pass

    async def on_schedule(self, event: ScheduleEvent):
        log.info("Schedule Report Generation")

        execution_timezone: str = self.config.dv_proc_timezone.value
        schedule: str = self.config.dv_proc_schedules.value

        if type(schedule) is not str:
            log.error(f"Schedule must be a string: {schedule}")
            return

        if not schedule.startswith("cron("):
            log.error(f"Schedule must be a cron expression: {schedule}")
            return

        if not schedule.endswith(")"):
            log.error(f"Schedule must be a cron expression: {schedule}")
            return

        cron = schedule[5:-1]

        execution_time = datetime.now(tz=ZoneInfo(execution_timezone)) - timedelta(
            minutes=5
        )

        iter = croniter.croniter(cron, execution_time)

        self.period_start = iter.get_prev(datetime)
        self.period_end = iter.get_next(datetime)

        if self.period_end - self.period_start < timedelta(hours=20):
            time_string = self.period_end.strftime("%H:%M:%S %d-%m-%Y")
        else:
            time_string = self.period_end.strftime("%d-%m-%Y")

        name = f"{self.received_deployment_config['APP_DISPLAY_NAME']} - {time_string}"
        self.devices = self.received_deployment_config.get("DEVICE_LIST", [])

        self._report_metadata = {
            "name": name,
            "devices": self.devices,
            "period_start": int(self.period_start.timestamp() * 1000),
            "period_end": int(self.period_end.timestamp() * 1000),
            "report_generator": "TODO",
            "status": "Generating",
            "logs": "",
        }

        log.info("Creating Message in Doover for Report")
        s = time.perf_counter()

        try:
            data = await self.api.publish_message(
                self.agent_id,
                "reports",
                self._report_metadata,
                organisation_id=self.agent_id,
            )
        except Exception as e:
            log.error(f"Error creating report message: {e}")
            return

        if "id" not in data:
            log.error("Error creating report message: cannot find id in response")
            return

        log.info(f"Message Creation took {time.perf_counter() - s} seconds.")

        self._report_id = data["id"]
        self.report_id = data["id"]

        log.info(f"Report ID: {self.report_id}")

        await self._generate(self.devices, self.period_start, self.period_end)

    async def on_manual_invoke(self, event: ManualInvokeEvent):
        
        if "report_id" not in event.payload:
            log.error("No Report Id provided")
            return
        
        self._report_id = event.payload["report_id"]
        self.report_id = event.payload["report_id"]
        
        try:
            data = await self.api.get_channel_message(
                self.agent_id,
                "reports",
                self.report_id,
                organisation_id=self.agent_id,
            )
        except Exception as e:
            log.error(f"Error getting report message: {e}")
            return
        
        self._report_metadata = data["data"]
        
        self.period_start = datetime.fromtimestamp(self._report_metadata["period_start"] / 1000.0)
        self.period_end = datetime.fromtimestamp(self._report_metadata["period_end"] / 1000.0)
        self.devices = self.received_deployment_config.get("DEVICE_LIST", [])
        
        await self._generate(self.devices, self.period_start, self.period_end) 

    async def _generate(
        self, agent_ids: list[int], period_start: datetime, period_end: datetime
    ):
        log.info(f"Start Report Generation from {period_start} to {period_end}")
        s = time.perf_counter()
        
        files = await self.generate(agent_ids, period_start, period_end)
        
        if type(files) is not list:
            files = [files]
        
        log.info(
            f"Report Generation took {time.perf_counter() - s} seconds. {len(files)} file{'s' if len(files) > 1 else ''} generated."
        )

        self._report_metadata["status"] = "Complete"

        log.info("Uploading Report to Doover")
        s = time.perf_counter()
        try:
            await self.api.update_message(
                self.agent_id,
                "reports",
                self._report_id,
                self._report_metadata,
                organisation_id=self.agent_id,
                files=files,
            )
        except Exception as e:
            log.error(f"Error creating report message: {e}")
            return
        log.info(f"Report Upload took {time.perf_counter() - s} seconds.")

    async def generate(
        self, agent_ids: list[int], period_start: datetime, period_end: datetime
    ):
        """Override this method to specify how a report should be generated.

        You do **not** need to call `super().generate()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def fetch_device_in_window(
        self,
        agent_id: int,
        channel_name: str,
        period_start: datetime,
        period_end: datetime,
    ):
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
        return await self.api.get_channel_messages(
            agent_id,
            channel_name,
            after=period_start,
            before=period_end,
            chunk_size=SPLIT_MESSAGES_LIMIT,
            organisation_id=self.agent_id,
        )

    async def fetch_devices_in_window(
        self,
        agent_ids: list[int],
        channel_name: str,
        period_start: datetime,
        period_end: datetime,
    ):
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
            tasks.append(
                self.fetch_device_in_window(
                    agent_id, channel_name, period_start, period_end
                )
            )

        # Collect the results
        results = await asyncio.gather(*tasks)

        # Return the results
        return {agent_id: result for agent_id, result in zip(agent_ids, results)}
