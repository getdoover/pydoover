import json
import time
import csv
from datetime import datetime
from os import PathLike
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pydoover.cloud.api import Client


class Message:
    """Represents a message in a channel.

    Attributes
    ----------
    id: str
        The unique identifier for the message.
    channel_id: str
        The unique identifier for the channel the message belongs to.
    agent_id: str
        The unique identifier for the agent that sent the message.
    channel_name: str
        The name of the channel the message belongs to.
    """

    def __init__(
        self,
        client: "Client",
        data: dict | str,
        channel_id: str = None,
        agent_id: str = None,
        channel_name: str = None,
    ):
        self.id = None
        self._timestamp: float = None

        self.client = client
        self.channel_id = channel_id
        self.agent_id = agent_id
        self.channel_name = channel_name
        self._payload = None

        if data is not None:
            self._from_data(data)

    def __repr__(self):
        if self._payload is not None:
            return f"<Message message_id={self.id}, payload={self._payload}>"
        return f"<Message message_id={self.id}>"

    def _from_data(self, data: dict[str, Any]):
        # {'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427', 'message': 'a7b493dd-4577-4f81-ac3d-f1b3be680b12', 'type': 'base', 'timestamp': 1715646840.250541}
        self.id = data.get("message", None)
        self.agent_id = data.get("agent", None)
        self.channel_name = data.get("channel_name", None)
        self._timestamp = data.get("timestamp", None)

        if not self.channel_id:
            self.channel_id = data.get("channel")

        self._payload = data.get("payload")

    def to_dict(self):
        return {
            "message": self.id,
            "agent": self.agent_id,
            "timestamp": self.timestamp,
            "channel": self.channel_id,
            "channel_name": self.channel_name,
            "payload": self._payload,
        }

    def update(self) -> None:
        """Fetches the latest data for the message from the server and updates the instance attributes."""
        data = self.client._get_message_raw(self.channel_id, self.id)
        self._from_data(data)

    def delete(self) -> None:
        """Deletes the message from the channel."""
        self.client._delete_message_raw(self.channel_id, self.id)

    def fetch_payload(self) -> dict | str:
        """Fetches the payload of the message from the site."""
        if self._payload is not None:
            return self._payload

        data = self.client._get_message_raw(self.channel_id, self.id)
        self._payload = json.loads(data["payload"])
        return self._payload

    @property
    def age(self) -> float:
        """Returns the age of the message in seconds since it was created."""
        return time.time() - self._timestamp

    @property
    def timestamp(self) -> datetime:
        """Returns the timestamp of the message as a datetime object in UTC."""
        return datetime.fromtimestamp(self._timestamp)

    def get_age(self) -> float:
        return time.time() - self._timestamp

    def get_timestamp(self) -> datetime:
        return datetime.fromtimestamp(self._timestamp)

    @staticmethod
    def from_csv_export(
        client: "Client", csv_file_path: str | PathLike
    ) -> list["Message"]:
        """Create a list of Message instances from a CSV export file.

        Parameters
        ----------
        client: Client
            The client instance to use for API interactions.
        csv_file_path: str
            The path to the CSV file containing the exported messages.

        Returns
        -------
        list[Message]
            A list of Message instances created from the CSV data.
        """

        messages = []

        # Open and read the CSV file using the csv module
        with open(csv_file_path, "r", newline="") as file:
            reader = csv.DictReader(file)  # Use DictReader to handle headers

            for row in reader:
                # Extract data from the row
                key = row["Key"]
                timestamp = row["Timestamp (UTC)"]
                channel_name = row["Channel"]
                channel_id = row["Channel ID"]
                # agent_name = row["Agent"]
                agent_id = row["Agent ID"]
                payload = row["Payload"]

                # Convert timestamp to UTC epoch timestamp
                timestamp = datetime.fromisoformat(timestamp).timestamp()

                # Create a Message instance
                message = Message(
                    client,
                    data=None,
                    channel_id=channel_id,
                    agent_id=agent_id,
                    channel_name=channel_name,
                )

                message.id = key
                message._timestamp = timestamp
                message._payload = json.loads(payload)

                messages.append(message)

        # Sort the messages by timestamp
        messages.sort(key=lambda x: x.timestamp)

        return messages
