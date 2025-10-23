import logging

from datetime import datetime, timezone
from typing import Any, Optional, Callable

import requests

from . import Agent, Channel, Message
from .application import Application
from .client import Route, AccessToken, RefreshToken
from ..api.exceptions import NotFound, Forbidden, HTTPException
from ...utils.snowflake import generate_snowflake_id_at

log = logging.getLogger(__name__)


class Client:
    """API Client for Doover Cloud"""

    def __init__(
        self,
        token: AccessToken,
        refresh_token: RefreshToken | None,
        base_url: str = "https://api.doover.com",
        data_base_url: str = "https://data.doover.com/api",
        auth_server_url: str = "https://auth.doover.com",
        auth_server_client_id: str = None,
        verify: bool = True,
        login_callback: Callable = None,
    ):
        self.access_token = token
        self.refresh_token = refresh_token

        self.verify = verify
        self.base_url = base_url
        self.data_base_url = data_base_url
        self.auth_server_url = auth_server_url
        self.auth_server_client_id = auth_server_client_id
        self.agent_id = None

        self.session = requests.Session()

        self.request_retries = 1
        self.request_timeout = 59

        self.update_headers()

        self.login_callback = login_callback

    def update_headers(self):
        self.session.headers.update(
            {"Authorization": f"Bearer {self.access_token.token}"}
        )
        self.session.verify = self.verify

    def request(self, route: Route, *, data_url: bool = False, **kwargs):
        if data_url:
            url = self.data_base_url + route.url
        else:
            url = self.base_url + route.url

        # default is access token to not expire
        if self.access_token.expires_at and self.access_token.expires_at < datetime.now(
            timezone.utc
        ):
            logging.info("Token expired, attempting to refresh token.")
            self.do_refresh_token()

        attempt_counter = 0
        retries = self.request_retries if route.method == "GET" else 0

        while attempt_counter <= retries:
            attempt_counter += 1

            log.debug(f"Making {route.method} request to {url} with kwargs {kwargs}")

            try:
                resp = self.session.request(
                    route.method, url, timeout=self.request_timeout, **kwargs
                )
            except requests.exceptions.Timeout:
                log.info(f"Request to {url} timed out.")
                if attempt_counter > retries:
                    raise HTTPException(f"Request timed out. {url}")
                continue

            if 200 <= resp.status_code < 300:
                # if we get a 200, we're good to go
                # this also accounts for any 200-range code.
                break
            elif resp.status_code == 401:
                raise Forbidden(f"Access denied. {url}, {resp.text}")
            elif resp.status_code == 403:
                raise Forbidden(f"Access denied. {url}")
            elif resp.status_code == 404:
                raise NotFound(f"Resource not found. {url}")

            log.info(
                f"Failed to make request to {url}. Status code: {resp.status_code}, message: {resp.text}"
            )
            if attempt_counter > retries:
                raise HTTPException(resp.text)

        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        log.debug(f"{url} has received {data}")
        return data

    @staticmethod
    def _parse_channel_id(channel_id: str):
        try:
            agent_id, name = channel_id.split(":")
        except ValueError:
            raise NotFound("Invalid channel ID format.")

        return int(agent_id), name

    def _get_agent_raw(self, agent_id: str) -> dict[str, Any]:
        return self.request(Route("GET", "/ch/v1/agent/{}/", agent_id))

    def _get_agent_list_raw(self) -> list[dict[str, Any]]:
        return self.request(Route("GET", "/ch/v1/list_agents/"))

    def get_agent(self, agent_id: str) -> Agent:
        data = self._get_agent_raw(agent_id)
        return data and Agent(client=self, data=data)

    def get_agent_list(self) -> list[Agent]:
        data = self._get_agent_list_raw()
        if "agents" not in data:
            return []
        return [Agent(client=self, data=d) for d in data["agents"]]

    def get_channel(self, channel_id: str) -> Channel:
        """Fetch a channel by its key.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.

        Returns
        -------
        Channel, Processor or Task
            The channel object, which can be a Channel, Processor or Task depending on the type of the channel.
        """
        agent_id, name = self._parse_channel_id(channel_id)
        return self.get_channel_named(name, agent_id)

    def _get_channel_named_raw(
        self, channel_name: str, agent_id: str
    ) -> dict[str, Any]:
        return self.request(
            Route("GET", "/agents/{}/channels/{}", agent_id, channel_name),
            data_url=True,
        )

    def get_channel_named(self, channel_name: str, agent_id: int) -> Channel:
        """Fetch a channel by its name, for a given agent.

        Parameters
        ----------
        channel_name : str
            The unique channel name for the channel.
        agent_id : str
            The unique identifier for the agent that owns the channel.

        Returns
        -------
        Channel
        """
        data = self._get_channel_named_raw(channel_name, agent_id)
        return data and Channel.from_data_v2(client=self, data=data)

    def get_channel_messages(
        self,
        channel_id: str,
        num_messages: int = None,
        before: int = None,
        after: int = None,
    ) -> list[Message]:
        """Fetch messages from a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel. For backwards compatibility with Doover 1.0, this is `agent_id:channel_name`.
        num_messages : int, optional
            The number of messages to fetch. If not provided, 50 messages will be fetched.
        before : int, optional
            A snowflake ID before which to fetch messages
        after : int, optional
            A snowflake ID after which to fetch messages

        Returns
        -------
        list[Message]
            A list of Message objects from the channel.
        """
        agent_id, name = self._parse_channel_id(channel_id)

        kwargs = {}
        if num_messages:
            kwargs["limit"] = num_messages
        if before:
            kwargs["before"] = before
        if after:
            kwargs["after"] = after

        data = self.request(
            Route("GET", "/agents/{}/channels/{}/messages", agent_id, name, **kwargs),
            data_url=True,
        )
        if not data:
            return []

        return [
            Message(client=self, data=m, channel_id=channel_id)
            for m in data["messages"]
        ]

    def _get_message_raw(
        self, agent_id: int, channel_name: str, message_id: str
    ) -> dict[str, Any]:
        return self.request(
            Route(
                "GET",
                "/agents/{}/channels/{}/messages/{}",
                agent_id,
                channel_name,
                message_id,
            ),
            data_url=True,
        )

    def get_channel_messages_in_window(
        self, channel_id: str, start: datetime, end: datetime
    ) -> list[Message]:
        """Fetch messages from a channel within a specific time window.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        start : datetime
            The start and end datetime objects defining the time window.
        end: datetime
            The start and end datetime objects defining the time window.
        """
        after, before = generate_snowflake_id_at(start), generate_snowflake_id_at(end)
        return self.get_channel_messages(channel_id, before=before, after=after)

    def get_message(self, channel_id: str, message_id: str) -> Optional[Message]:
        """Fetch a message by its ID from a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        message_id : str
            The unique identifier for the message.

        Returns
        -------
        Message
            The message object.

        Raises
        ------
        NotFound
            If the message does not exist in the channel.
        """
        agent_id, name = self._parse_channel_id(channel_id)
        data = self._get_message_raw(agent_id, channel_id, message_id)
        return data and Message(client=self, data=data, channel_id=channel_id)

    def _delete_message_raw(self, channel_id: str, message_id: int) -> bool:
        agent_id, name = self._parse_channel_id(channel_id)
        return self.request(
            Route(
                "DELETE",
                "/agents/{}/channels/{}/messages/{}",
                agent_id,
                name,
                message_id,
            ),
            data_url=True,
        )

    def create_channel(self, channel_name: str, agent_id: str) -> Channel:
        """Create a channel with the given name for the specified agent.

        If the channel already exists, it will return the existing channel.

        Parameters
        ----------
        channel_name : str
            The unique name for the channel.
        agent_id : str
            The owner agent's unique identifier.

        Returns
        -------
        Channel

        """
        try:
            return self.get_channel_named(channel_name, agent_id)
        except NotFound:
            pass

        self.request(
            Route("POST", "/agents/{}/channels/{}", agent_id, channel_name),
            data_url=True,
        )
        # this is a bit of a wasted API call, but since this is the same method to post an aggregate to a
        # channel it can either return a new channel ID (if created), or the message ID of the posted message.
        return self.get_channel_named(channel_name, agent_id)

    def create_processor(self, processor_name: str, agent_id: str):
        raise RuntimeError("processors not supported in pydoover yet")

    def create_task(self, task_name: str, agent_id: str, processor_id: str):
        raise RuntimeError("tasks not supported in pydoover yet")

    def _maybe_subscribe_to_channel(
        self, channel_id: str, task_id: str, subscribe: bool
    ):
        raise RuntimeError("subscriptions not supported in api yet")

    def subscribe_to_channel(self, channel_id: str, task_id: str) -> bool:
        """Subscribe a task to a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        task_id : str
            The unique identifier for the task.

        Returns
        -------
        bool
            True if the subscription was successful, False otherwise.
        """
        return self._maybe_subscribe_to_channel(channel_id, task_id, True)

    def unsubscribe_from_channel(self, channel_id: str, task_id: str) -> bool:
        """Unsubscribe a task from a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        task_id : str
            The unique identifier for the task.

        Returns
        -------
        bool
            True if the unsubscription was successful, False otherwise.
        """
        return self._maybe_subscribe_to_channel(channel_id, task_id, False)

    def publish_to_channel(
        self,
        channel_id: str,
        data: Any,
        save_log: bool = True,
        log_aggregate: bool = False,
        override_aggregate: bool = False,
        timestamp: Optional[datetime] = None,
    ):
        """Publish data to a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        data : Any
            The data to publish to the channel. This can be a string or a dictionary.
        save_log : bool, optional
            Whether to save the log of the message. Defaults to True.
        log_aggregate : bool, optional
            Whether to aggregate the log of the message. Defaults to False.
        override_aggregate : bool, optional
            Whether to override any existing aggregate with a completely fresh new message
        timestamp : datetime, optional
            The timestamp to set for the message. If not provided, the current time will be used.
        """
        agent_id, name = self._parse_channel_id(channel_id)

        #     pub data: Value,
        #     pub record_log: bool,
        #     pub is_diff: bool,
        #     pub ts: Option<u64>,
        data = {
            "data": data,
            "record_log": save_log,
            "is_diff": False if override_aggregate is True else True,
        }
        if timestamp:
            data["ts"] = int(timestamp.timestamp() * 1000)

        return self.request(
            Route("POST", "/agents/{}/channels/{}/messages", agent_id, name),
            json=data,
            data_url=True,
        )

    def publish_to_channel_name(
        self,
        agent_id: str,
        channel_name: str,
        data: Any,
        save_log: bool = True,
        log_aggregate: bool = False,
        override_aggregate: bool = False,
        timestamp: Optional[datetime] = None,
    ):
        """Publish data to a channel by its name.

        Parameters
        ----------
        agent_id : str
            The agent ID who owns this channel.
        channel_name : str
            The name for the channel.
        data : Any
            The data to publish to the channel. This can be a string or a dictionary.
        save_log : bool, optional
            Whether to save the log of the message. Defaults to True.
        log_aggregate : bool, optional
            Whether to aggregate the log of the message. Defaults to False.
        override_aggregate : bool, optional
            Whether to override any existing aggregate with a completely fresh new message
        timestamp : datetime, optional
            The timestamp to set for the message. If not provided, the current time will be used.
        """
        self.publish_to_channel(
            f"{agent_id}:{channel_name}",
            data,
            save_log,
            log_aggregate,
            override_aggregate,
            timestamp,
        )

    def create_tunnel_endpoints(self, agent_id: str, endpoint_type: str, amount: int):
        raise RuntimeError("creating tunnel endpoints not supported on doover 2.0")

    def get_tunnel_endpoints(self, agent_id: str, endpoint_type: str):
        raise RuntimeError("listing tunnel endpoints not supported on doover 2.0")

    def get_tunnel(self, tunnel_id: str):
        device_id, tunnel_id = tunnel_id.split(":")
        # raise RuntimeError("getting specific tunnel not supported (yet).")
        return self.request(
            Route("GET", "/devices/{}/tunnels/{}", device_id, tunnel_id)
        )

    def get_tunnels(self, agent_id: str, show_choices: bool = False):
        return self.request(Route("GET", "/devices/{}/tunnels", agent_id))

    def create_tunnel(self, agent_id: str, **data):
        return self.request(Route("POST", "/devices/{}/tunnels/", agent_id), json=data)

    def patch_tunnel(self, tunnel_id: str, **data):
        device_id, tunnel_id = tunnel_id.split(":")
        return self.request(
            Route("PATCH", "/devices/{}/tunnels/{}/", device_id, tunnel_id), json=data
        )

    def activate_tunnel(self, tunnel_id: str):
        device_id, tunnel_id = tunnel_id.split(":")
        return self.request(
            Route("POST", "/devices/{}/tunnels/{}/activate/", device_id, tunnel_id)
        )

    def deactivate_tunnel(self, tunnel_id: str):
        device_id, tunnel_id = tunnel_id.split(":")
        return self.request(
            Route("POST", "/ch/v1/tunnels/{}/deactivate/", device_id, tunnel_id)
        )

    def delete_tunnel(self, tunnel_id: str):
        device_id, tunnel_id = tunnel_id.split(":")
        return self.request(
            Route("DELETE", "/devices/{}/tunnels/{}/", device_id, tunnel_id)
        )

    # applications. only supports operations on apps, not installs / deployments at the moment.
    def get_applications(self):
        """Get the list of applications available to the current agent."""
        return self.request(Route("GET", "/applications/"))

    def create_application(
        self, application: Application, is_staging: bool = False
    ) -> str:
        """Create a new application with the given data."""
        payload = application.to_dict(
            include_deployment_data=True, is_staging=is_staging
        )

        headers = {}
        if payload["owner_org_id"]:
            headers["X-Doover-Organisation"] = str(payload["owner_org_id"])

        data = self.request(
            Route("POST", "/applications/"),
            json=payload,
            headers=headers,
        )
        return data["id"]

    def get_application(self, key: str) -> Application:
        """Get a specific application by its key."""
        data = self.request(Route("GET", "/applications/{}/", key))
        return Application.from_data(data=data)

    def update_application(
        self, application: Application, is_staging: bool = False
    ) -> None:
        """Update an existing application with the given data."""
        payload = application.to_dict(
            include_deployment_data=True, is_staging=is_staging
        )
        return self.request(
            Route("PATCH", "/applications/{}/", payload["id"]),
            json=payload,
        )

    def publish_processor_source(self, app_id: int, content: bytes):
        return self.request(
            Route("PUT", "/applications/{}/processor_source/", app_id),
            files={"file": content},
        )

    def create_processor_version(self, app_id: int):
        return self.request(
            Route("POST", "/applications/{}/processor_version/", app_id)
        )

    def do_refresh_token(self):
        resp = requests.post(
            f"{self.auth_server_url}/oauth2/token",
            params={
                "grant_type": "refresh_token",
                "access_token": self.access_token.token,
                "refresh_token": self.refresh_token.token,
                "client_id": self.auth_server_client_id,
            },
        )

        if resp.ok:
            data = resp.json()
            log.info("Refreshed access token.")
            self.access_token = AccessToken(data["access_token"], data["expires_in"])
            self.update_headers()
            self.login_callback()
        else:
            print("Failed to refresh access token.")
            resp.raise_for_status()

    def login(self):
        return True
