import requests
import json
import copy
from datetime import datetime, timezone
from math import floor

from . import json_flatten

# Module-level constants
SECS_IN_DAY = 24 * 60 * 60
CHANNEL_NAME = "ui_state"


class ReportGeneratorDooverDataMixin:
    """
    Mixin class for adding capabilities for retrieving data from the Doover API to a report generator.
    """

    @staticmethod
    def get_data_object(payload_dict, data_object_name):
        """
        Extract a specific data object from the flattened JSON payload.
        """
        reported_state = payload_dict["state"].get("reported", payload_dict["state"])
        reported_flattened = json_flatten.flatten(reported_state)
        flat_object_key = None

        for key in reported_flattened:
            parts = key.split(".")
            if (
                parts
                and parts[-1] == "name"
                and reported_flattened[key].lower() == data_object_name.lower()
            ):
                flat_object_key = ".".join(parts[:-1])
                break
            elif len(parts) > 2 and parts[-2].lower() == data_object_name.lower():
                flat_object_key = ".".join(parts[:-1])
                break
            elif (
                len(parts) > 3
                and parts[-3].lower() == data_object_name.lower()
                and parts[-2] == "currentValue"
            ):
                flat_object_key = ".".join(parts[:-2])
                break

        if flat_object_key is None:
            return None

        relevant = {}
        for key in reported_flattened:
            if flat_object_key in key:
                trimmed = key.replace(flat_object_key, "", 1)
                if trimmed.startswith("."):
                    trimmed = trimmed[1:]
                relevant[trimmed] = reported_flattened[key]
        return json_flatten.unflatten(relevant)

    @staticmethod
    def add_to_message_log(message, name, object):
        """
        Add a field to a message log for a specific object.
        """
        if "payload" in message:
            if "state" in message["payload"]:
                if "children" in message["payload"]["state"]:
                    message["payload"]["state"]["children"][name] = object
                elif "reported" in message["payload"]["state"]:
                    message["payload"]["state"]["reported"][name] = object
                else:
                    message["payload"]["state"][name] = object
            else:
                message["payload"][name] = object
        else:
            message[name] = object

        return message

    @staticmethod
    def get_available_dataseries(payload_dict):
        """
        Return available data series (uiVariables) from the aggregate payload.
        """
        reported_state = payload_dict["state"].get("reported", payload_dict["state"])
        reported_flattened = json_flatten.flatten(reported_state)
        series_names = []

        for key, value in reported_flattened.items():
            if ".type" in key and value == "uiVariable":
                var_type_key = key.replace(".type", ".varType")
                if (
                    var_type_key in reported_flattened
                    and reported_flattened[var_type_key] == "time"
                ):
                    continue  # Skip time variables
                name_key = key.replace(".type", ".name")
                series_names.append(reported_flattened[name_key])

        result = []
        for series_name in series_names:
            result.append(
                ReportGeneratorDooverDataMixin.get_data_object(
                    payload_dict, series_name
                )
            )
        return result

    def get_current_server_time(self, agent_id):
        """
        Get the current server time (in seconds since the epoch) via the API.
        """
        url = f"{self.api_endpoint}/ch/v1/agent/{agent_id}/"
        resp = requests.get(
            url,
            headers={"Authorization": "Token " + str(self.access_token)},
            verify=(not self.test_mode),
        )
        if resp.status_code == 200:
            result = json.loads(resp.text)
            return int(result["current_time"])
        elif resp.status_code == 403:
            raise Exception("Access Denied - Check Token is Current")
        else:
            self.add_to_log(f"Server Error : {resp.status_code}")
            raise Exception("Server Error")

    def get_current_data_aggregate(self, agent_id):
        """
        Get the current data aggregate from the API.
        """
        url = f"{self.api_endpoint}/ch/v1/agent/{agent_id}/{CHANNEL_NAME}/"
        resp = requests.get(
            url,
            headers={"Authorization": "Token " + str(self.access_token)},
            verify=(not self.test_mode),
        )
        if resp.status_code != 200:
            self.add_to_log(f"Server Error : {resp.status_code}")
            raise Exception("Server Error " + str(resp.status_code))
        data = json.loads(resp.text)
        return data["aggregate"]["payload"]

    def _get_data_for_window(self, window_start, window_end, agent_id):
        """
        Retrieve data messages for a specific time window.
        """
        window_start = int(window_start)
        window_end = int(window_end)
        self.add_to_log(f"Getting data between {window_start} - {window_end}")

        url = (
            f"{self.api_endpoint}/ch/v1/agent/{agent_id}/{CHANNEL_NAME}/"
            f"messages/time/{window_start}/{window_end}/"
        )
        resp = requests.get(
            url,
            headers={"Authorization": "Token " + str(self.access_token)},
            verify=(not self.test_mode),
        )
        if resp.status_code != 200:
            self.add_to_log(f"Server Error : {resp.status_code}")
            raise Exception("Server Error " + str(resp.status_code))
        data = json.loads(resp.text)
        msgs = data["messages"]
        msgs.reverse()  # Order messages from earliest to latest
        return msgs

    def retrieve_data(self, period_from, period_to, agent_id):
        """
        Retrieve data messages over the specified period by splitting the time window into full days
        and any remaining fraction.
        """
        curr_server_time = int(self.get_current_server_time(agent_id))
        local_time = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
        time_diff = curr_server_time - local_time

        start_secs = (
            copy.copy(period_from).replace(tzinfo=self.for_timezone).timestamp()
            + time_diff
        )
        end_secs = (
            copy.copy(period_to).replace(tzinfo=self.for_timezone).timestamp()
            + time_diff
        )

        num_days = (end_secs - start_secs) / SECS_IN_DAY
        self.add_to_log(f"{num_days} days")

        msgs = []
        for day in range(floor(num_days)):
            temp_start = start_secs + day * SECS_IN_DAY
            temp_end = temp_start + SECS_IN_DAY
            msgs.extend(self._get_data_for_window(temp_start, temp_end, agent_id))

        remainder = num_days % 1
        if remainder > 0:
            remainder_secs = int(remainder * SECS_IN_DAY)
            msgs.extend(
                self._get_data_for_window(end_secs - remainder_secs, end_secs, agent_id)
            )
        return msgs
