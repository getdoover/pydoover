import asyncio
import logging
import os
import re
import time

from datetime import datetime, timedelta, timezone
from itertools import chain
from zoneinfo import ZoneInfo

try:
    import croniter
except ImportError:
    HAS_CRONITER = False
else:
    HAS_CRONITER = True

from ..utils.files import zip_files

from ..models import (
    ManualInvokeEvent,
    MessageCreateEvent,
    DeploymentEvent,
    ScheduleEvent,
    File,
)
from ..processor.application import Application as ApplicationBase

log = logging.getLogger(__name__)

SPLIT_MESSAGES_LIMIT = 100  # 1 hour
MAX_FILE_SIZE = 4.5e7


class Application(ApplicationBase):
    def __init__(self):
        super().__init__()

        self.period_start = None
        self.period_end = None
        self.devices = None

    async def on_message_create(self, event: MessageCreateEvent):
        raise RuntimeError("Report Generator does not support message create events")

    async def on_deployment(self, event: DeploymentEvent):
        pass

    async def on_schedule(self, event: ScheduleEvent):
        log.info("Schedule Report Generation")

        execution_timezone: str = self.config.dv_proc_timezone.value
        schedule: str = self.config.dv_proc_schedules.value

        if not isinstance(schedule, str):
            log.error(f"Schedule must be a string: {schedule}, not '{type(schedule)}'")
            return

        m = re.fullmatch(r"cron\((.*)\)", schedule)
        if not m:
            log.error(f"Schedule must be a cron expression: {schedule}")
            return

        cron = m.group(1)

        execution_time = datetime.now(tz=ZoneInfo(execution_timezone)) - timedelta(
            minutes=5
        )

        if not HAS_CRONITER:
            raise RuntimeError("croniter dependency is required for report generation")

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
            "report_generator": os.environ.get("APPLICATION_ID", ""),
            "config": self.received_deployment_config,
            "status": "Generating",
            "logs": "",
        }

        log.info("Creating Message in Doover for Report")
        s = time.perf_counter()

        try:
            data = await self.api.create_message(
                "reports",
                self._report_metadata,
                organisation_id=self.agent_id,
            )
        except Exception as e:
            log.error(f"Error creating report message: {e}")
            return

        log.info(f"Message Creation took {time.perf_counter() - s} seconds.")

        self._report_id = self.report_id = data.id
        log.info(f"Report ID: {self.report_id}")

        await self._generate(self.devices, self.period_start, self.period_end)

    async def on_manual_invoke(self, event: ManualInvokeEvent):
        if "report_id" not in event.payload:
            log.error("No Report Id provided")
            return

        self.report_id = self._report_id = event.payload["report_id"]

        try:
            data = await self.api.fetch_message(
                "reports",
                self.report_id,
                organisation_id=self.agent_id,
            )
        except Exception as e:
            log.error(f"Error getting report message: {e}")
            return

        self._report_metadata = data.data

        self.period_start = datetime.fromtimestamp(
            self._report_metadata["period_start"] / 1000.0,
            tz=timezone.utc,
        )
        self.period_end = datetime.fromtimestamp(
            self._report_metadata["period_end"] / 1000.0,
            tz=timezone.utc,
        )
        self.devices = self.received_deployment_config.get("DEVICE_LIST", [])

        await self._generate(self.devices, self.period_start, self.period_end)

    async def _generate(
        self, agent_ids: list[int], period_start: datetime, period_end: datetime
    ):
        log.info(f"Start Report Generation from {period_start} to {period_end}")
        s = time.perf_counter()

        try:
            files = await self.generate(agent_ids, period_start, period_end)
        except Exception as e:
            log.error(f"Error generating report: {e}", exc_info=e)

            self._report_metadata["logs"] = self.log_capture_string.getvalue()

            await self.api.update_message(
                "reports",
                self._report_id,
                self._report_metadata,
                organisation_id=self.agent_id,
            )
            return

        if not isinstance(files, list):
            files = [files]

        log.info(
            f"Report Generation took {time.perf_counter() - s} seconds. {len(files)} file{'s' if len(files) > 1 else ''} generated."
        )

        self._report_metadata["status"] = "Complete"

        log.info("Uploading Report to Doover")

        total_file_size = sum(f.size for f in files)

        if total_file_size > MAX_FILE_SIZE:
            log.info(
                f"Report is {total_file_size} bytes, which is over the 45MB limit. Zipping files."
            )
            files = zip_files(files)

        s = time.perf_counter()

        self._report_metadata["logs"] = self.log_capture_string.getvalue()

        try:
            await self.api.update_message(
                "reports",
                self._report_id,
                self._report_metadata,
                organisation_id=self.agent_id,
                files=files,
            )
        except Exception as e:
            log.error(f"Error updating report message: {e}")
            try:
                self._report_metadata["status"] = "Failed"
                await self.api.update_message(
                    "reports",
                    self._report_id,
                    self._report_metadata,
                    organisation_id=self.agent_id,
                )
            except Exception as e:
                log.error(f"Error updating report message without files: {e}")
            return
        log.info(f"Report Upload took {time.perf_counter() - s} seconds.")

    async def generate(
        self, agent_ids: list[int], period_start: datetime, period_end: datetime
    ) -> list[File] | File:
        """Override this method to specify how a report should be generated.

        You do **not** need to call `super().generate()` as this function ordinarily does nothing.
        """
        return NotImplemented

    async def fetch_messages(
        self,
        channel_name: str,
        period_start: datetime,
        period_end: datetime,
        agent_ids: list[int],
    ):
        """Fetch messages from multiple agents for a channel within a time window.

        This should probably use some sort of batch endpoint but I don't have one yet...
        """
        data = await asyncio.gather(
            *[
                self.api.iter_messages(
                    channel_name,
                    agent_id=agent_id,
                    before=period_end,
                    after=period_start,
                ).collect()
                for agent_id in agent_ids
            ]
        )
        return await self.filter_messages(chain(*data))

    async def filter_messages(self, data):
        # this allows subclasses to easily filter out specific messages... or combine, etc..
        # will become more useful / easy when we move to tag_values...
        return list(data)
