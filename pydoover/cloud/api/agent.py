from contextlib import suppress

from .channel import Channel


class Agent:
    """Represents an agent in the Doover site.

    Attributes
    ----------
    key: str
        The unique identifier for the agent.
    type: str
        The type of the agent, e.g., "doover_users | user".
    name: str
        The name of the agent, if available.
    owner_org: str
        The organization that the agent belongs to.
    deployment_config: dict
        The deployment configuration for the agent, if available.
    channels: list[Channel]
        A list of channels associated with the agent.
    """

    def __init__(self, client, data):
        self.client = client

        self.id = None
        self.key = None
        self.type = None
        self.name = None
        self.owner_org = None
        self.deployment_config = None
        self.channels = None

        self._from_data(data)

    def _from_data(self, data):
        # {'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427', 'current_time': 1715662485.485132, 'type': 'doover_users | user', 'channels': [{'channel': 'd1c7e8e3-f47b-4c68-86d7-65054d9e97d3', 'name': 'josh-test', 'type': 'base', 'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427'}, {'channel': '1f71b8bd-9444-4f34-859f-f339875a765c', 'name': 'test-logs', 'type': 'base', 'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427'}, {'channel': '86c96181-425d-46f4-a4eb-b36bde2b3984', 'name': 'notifications', 'type': 'base', 'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427'}]}
        self.id = data["agent"]
        self.key = data["agent"]

        self.type = data["type"]

        with suppress(KeyError):
            self.name = data["name"]

        with suppress(KeyError):
            self.owner_org = data["owner_org"]

        with suppress(KeyError):
            self.deployment_config = data["settings"]["deployment_config"]

        self.channels = [
            Channel(data=c, client=self.client) for c in data.get("channels", [])
        ]

    @property
    def agent_id(self):
        """Returns the unique identifier for the agent."""
        return self.id

    def update(self):
        """Fetches the latest data for the agent from the API and updates the instance attributes."""
        res = self.client._get_agent_raw(self.id)
        return self._from_data(res)
