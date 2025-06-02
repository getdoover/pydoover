#!/usr/bin/env python3
import os
from datetime import datetime

from .data import ReportGeneratorDooverDataMixin


class ReportGeneratorBase:
    """
    Report generator that creates reports for given agents within a specified time period.

    Attributes:
        tmp_workspace (str): Temporary workspace path.
        access_token (str): API access token.
        agent_ids (list): List of agent IDs.
        agent_display_names (list): List of agent display names.
        period_from (datetime): Start of the period (in UTC).
        period_to (datetime): End of the period (in UTC).
        for_timezone (pytz.timezone): Timezone for localizing the report.
        logging_function (callable): Optional function for logging.
        progress_update_function (callable): Optional function to update progress.
        api_endpoint (str): API endpoint.
        report_name (str): Name of the report.
        test_mode (bool): Flag for test mode.
    """

    def __init__(
        self,
        tmp_workspace: str,
        access_token: str,
        agent_ids: list,
        agent_display_names: list,
        period_from_utc: datetime,
        period_to_utc: datetime,
        for_timezone,
        logging_function=None,
        progress_update_function=None,
        api_endpoint: str = None,
        report_name: str = None,
        test_mode: bool = False,
    ):
        self.tmp_workspace = tmp_workspace
        self.access_token = access_token
        self.agent_ids = agent_ids
        self.agent_display_names = agent_display_names
        self.period_from = period_from_utc  # UTC datetime
        self.period_to = period_to_utc  # UTC datetime
        self.for_timezone = for_timezone
        self.logging_function = logging_function
        self.progress_update_function = progress_update_function
        self.api_endpoint = api_endpoint
        self.report_name = report_name
        self.test_mode = test_mode

        self._localize_period()

        if self.logging_function:
            self.logging_function("Report Generator Initialized")
            self.logging_function(f"Agents = {self.agent_ids}")
            self.logging_function(f"Start Period = {self.period_from}")
            self.logging_function(f"End Period = {self.period_to}")
            self.logging_function(f"For Timezone = {self.for_timezone}")

    def update_progress(self, progress: float, *args, **kwargs) -> None:
        """
        Update the progress of the report generation.

        Args:
            progress (float): Progress value between 0 and 1.
        """
        if self.progress_update_function:
            self.progress_update_function(progress, *args, **kwargs)

    def _localize_period(self):
        """
        Localize the UTC period to the desired timezone.
        Returns a tuple (localized_period_from, localized_period_to).
        """
        period_from_naive = self.period_from.replace(tzinfo=None)
        period_to_naive = self.period_to.replace(tzinfo=None)

        if self.for_timezone:
            localized_period_from = self.for_timezone.fromutc(period_from_naive)
            localized_period_to = self.for_timezone.fromutc(period_to_naive)
        else:
            localized_period_from = period_from_naive
            localized_period_to = period_to_naive

        self.localized_period_from = localized_period_from
        self.localized_period_to = localized_period_to

        return localized_period_from, localized_period_to

    def assess_progress(self, progress: float, agent_id: str = None) -> None:
        """
        Assess the progress of the report generation.

        Args:
            progress (float): Progress value between 0 and 1.
            agent_id (str): The optional id of the agent currently in question
        """
        if not agent_id:
            self.update_progress(progress)
            return

        ## Update as if doing multiple reports for each individual agent
        try:
            ind = self.agent_ids.index(agent_id)
        except ValueError:
            if self.logging_function:
                self.logging_function(
                    f"Agent ID {agent_id} not found in the agent list."
                )
            self.update_progress(progress)
            return

        full_len = len(self.agent_ids)
        total_progress = (ind / full_len) + (progress / full_len)

        self.update_progress(total_progress)

    ## Abstract methods to optionally define
    # def generate_one(self, agent_id: str) -> None:
    #     """
    #     Generate a report for a single agent.
    #     """
    #     pass

    def generate(self) -> None:
        """
        Generate a report
        This is designed to either be called directly or to be overridden by a subclass.

        Generally speaking, users should either override this method or the generate_for_one_agent method.
        """
        if self.logging_function:
            self.logging_function("Generating report...")

        if hasattr(self, "generate_one"):
            for agent_id in self.agent_ids:
                self.assess_progress(0.01, agent_id)
                self.generate_one(agent_id)
                self.assess_progress(1.0, agent_id)
        else:
            if self.logging_function:
                self.logging_function("No report generation method defined.")

    def get_agent_display_name(self, agent_id: str) -> str:
        """
        Get the display name for an agent based on its ID.
        """
        try:
            ind = self.agent_ids.index(agent_id)
        except ValueError:
            return None

        return self.agent_display_names[ind]

    def add_to_log(self, msg):
        """
        Log a message via the provided logging_function (or print if not provided).
        """
        if self.logging_function is not None:
            self.logging_function(msg)
        else:
            print(msg)

    def get_ws_path(self, *args) -> str:
        """
        Get the path to a file in the temporary workspace.
        """
        if self.tmp_workspace is None:
            return os.path.join(*args)
        return os.path.join(self.tmp_workspace, *args)

    def get_file_outputs(self) -> list:
        """
        Returns a list of expected output filenames for each agent.
        """
        return [f"{name}.xlsx" for name in self.agent_display_names]

    def get_output_message(self) -> str:
        """
        Returns the output message after report generation.
        """
        return "Report generated"


class ReportGenerator(ReportGeneratorBase, ReportGeneratorDooverDataMixin):
    pass


generator = ReportGenerator
