import logging

from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar
from urllib.parse import quote, urlencode

import requests

from .message import Message
from .agent import Agent
from .application import Application
from .channel import Channel, Processor, Task
from .config import ConfigManager
from .exceptions import NotFound, Forbidden, HTTPException


log = logging.getLogger(__name__)
AccessToken = namedtuple("AccessToken", ["token", "expires_at"], defaults=(None,))
T = TypeVar("T", bound=Channel)


class Route:
    def __init__(self, method, route, *args, **kwargs):
        self.method = method

        self.url = route
        if args:
            self.url = route.format(*[quote(a) for a in args])

        if kwargs:
            self.url = f"{self.url}?{urlencode(kwargs)}"


class Client:
    """API Client for Doover Cloud"""

    def __init__(
        self,
        username: str = None,
        password: str = None,
        token: str = None,
        token_expires: datetime = None,
        base_url: str = "https://my.doover.dev",
        agent_id: str = None,
        verify: bool = True,
        login_callback: Callable = None,
        config_profile: str = "default",
        debug: bool = False,
    ):
        self.access_token = None
        if token:
            self.access_token = AccessToken(token, token_expires)

        self.agent_id = agent_id
        self.login_callback = login_callback

        self.username = username
        self.password = password

        self.verify = verify
        self.base_url = base_url
        self.session = requests.Session()

        self.request_retries = 1
        self.request_timeout = 59

        if debug:
            logging.basicConfig(level=logging.DEBUG)

        if not ((username and password) or token):
            self.config_manager = ConfigManager(config_profile)
            self.config_manager.read()

            config = self.config_manager.current
            if not config:
                raise RuntimeError(
                    f"No configuration found for profile {self.config_manager.current_profile}. "
                    f"Please specify a profile with the `config_profile` parameter, "
                    f"manually set a token or `doover login`"
                )

            self.agent_id = config.agent_id
            self.username = config.username
            self.password = config.password
            self.access_token = AccessToken(config.token, config.token_expires)
            self.base_url = config.base_url

        if self.access_token:
            self.update_headers()

    def has_persistent_connection(self):
        return False

    def update_headers(self):
        self.session.headers.update(
            {"Authorization": f"Token {self.access_token.token}"}
        )
        self.session.verify = self.verify

    def request(self, route: Route, **kwargs):
        # default is access token to not expire
        if (
            self.access_token.expires_at
            and self.access_token.expires_at < datetime.utcnow()
        ):
            logging.info("Token expired, attempting to refresh token.")
            self.login()

        url = self.base_url + route.url

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

    def _get_agent_raw(self, agent_id: str) -> dict[str, Any]:
        return self.request(Route("GET", "/ch/v1/agent/{}/", agent_id))

    def _get_agent_list_raw(self) -> list[dict[str, Any]]:
        return self.request(Route("GET", "/ch/v1/list_agents/"))

    def get_agent(self, agent_id: str) -> Agent:
        """Fetches an agent by its key.

        Parameters
        ----------
        agent_id : str
            The unique identifier for the agent.

        Returns
        -------
        Agent
            The agent object.

        Raises
        ------
        NotFound
            You don't have permission to access this agent.
        """
        data = self._get_agent_raw(agent_id)
        return data and Agent(client=self, data=data)

    def get_agent_list(self) -> list[Agent]:
        """Fetches a list of all agents you have access to.

        Returns
        -------
        list[Agent]
            A list of Agents that you have access to.
        """
        data = self._get_agent_list_raw()
        if "agents" not in data:
            return []
        return [Agent(client=self, data=d) for d in data["agents"]]

    def _parse_channel(self, data) -> T:
        if data["name"].startswith("!"):
            return Task(client=self, data=data)
        elif data["name"].startswith("#"):
            return Processor(client=self, data=data)
        else:
            return Channel(client=self, data=data)

    def _get_channel_raw(self, channel_id: str) -> dict[str, Any]:
        return self.request(Route("GET", "/ch/v1/channel/{}/", channel_id))

    def get_channel(self, channel_id: str) -> Optional[T]:
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
        data = self._get_channel_raw(channel_id)
        return data and self._parse_channel(data)

    def _get_channel_named_raw(
        self, channel_name: str, agent_id: str
    ) -> dict[str, Any]:
        return self.request(Route("GET", "/ch/v1/agent/{}/{}/", agent_id, channel_name))

    def get_channel_named(self, channel_name: str, agent_id: str) -> Optional[T]:
        """Fetch a channel by its name, for a given agent.

        Parameters
        ----------
        channel_name : str
            The unique channel name for the channel.
        agent_id : str
            The unique identifier for the agent that owns the channel.

        Returns
        -------
        Channel, Processor or Task
            The channel object, which can be a Channel, Processor or Task depending on the type of the channel.
        """
        data = self._get_channel_named_raw(channel_name, agent_id)
        return data and self._parse_channel(data)

    def get_channel_messages(
        self, channel_id: str, num_messages: Optional[int] = None
    ) -> list[Message]:
        """Fetch messages from a channel.

        Parameters
        ----------
        channel_id : str
            The unique identifier for the channel.
        num_messages : int, optional
            The number of messages to fetch. If not provided, all messages will be fetched.

        Returns
        -------
        list[Message]
            A list of Message objects from the channel.
        """
        if num_messages:
            data = self.request(
                Route(
                    "GET",
                    "/ch/v1/channel/{}/messages/{}/",
                    channel_id,
                    str(num_messages),
                )
            )
        else:
            data = self.request(Route("GET", "/ch/v1/channel/{}/messages/", channel_id))

        if not data:
            return []

        return [
            Message(client=self, data=m, channel_id=channel_id)
            for m in data["messages"]
        ]

    def _get_message_raw(self, channel_id: str, message_id: str) -> dict[str, Any]:
        return self.request(
            Route("GET", "/ch/v1/channel/{}/message/{}", channel_id, message_id)
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
        start = str(int(start.timestamp()))
        end = str(int(end.timestamp()))
        data = self.request(
            Route(
                "GET", "/ch/v1/channel/{}/messages/time/{}/{}/", channel_id, start, end
            )
        )
        if not data:
            return []

        return [
            Message(client=self, data=m, channel_id=channel_id)
            for m in data["messages"]
        ]

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
        data = self._get_message_raw(channel_id, message_id)
        return data and Message(client=self, data=data, channel_id=channel_id)

    def _delete_message_raw(self, channel_id: str, message_id: str) -> bool:
        return self.request(
            Route("DELETE", "/ch/v1/channel/{}/message/{}", channel_id, message_id)
        )

    def create_channel(self, channel_name: str, agent_id: str) -> T:
        """Create a channel with the given name for the specified agent.

        If the channel already exists, it will return the existing channel.

        Parameters
        ----------
        channel_name : str
            The unique name for the channel. Should start with a '#' for processors or '!' for tasks.
        agent_id : str
            The owner agent's unique identifier.

        Returns
        -------
        Channel, Processor or Task
            The channel object, which can be a Channel, Processor or Task depending on the type of the channel.

        """
        try:
            return self.get_channel_named(channel_name, agent_id)
        except NotFound:
            pass
        # all we need to do is publish to a channel with an empty payload
        self.request(Route("POST", "/ch/v1/agent/{}/{}/", agent_id, channel_name))
        # this is a bit of a wasted API call, but since this is the same method to post an aggregate to a
        # channel it can either return a new channel ID (if created), or the message ID of the posted message.
        return self.get_channel_named(channel_name, agent_id)

    def create_processor(self, processor_name: str, agent_id: str) -> Processor:
        """Create a processor channel with the given name for the specified agent.

        If the processor already exists, it will return the existing processor.

        Parameters
        ----------
        processor_name : str
            The unique name for the processor channel.
        agent_id : str
            The owner agent's unique identifier.

        Returns
        -------
        Processor
            The processor channel object.
        """
        return self.create_channel("#" + processor_name.lstrip("#"), agent_id)

    def create_task(self, task_name: str, agent_id: str, processor_id: str) -> Task:
        """Create a task channel with the given name for the specified agent and an associated processor.

        Parameters
        ----------
        task_name : str
            The unique name for the task channel.
        agent_id : str
            The owner agent's unique identifier.
        processor_id : str
            The processor to associate with this task

        Returns
        -------
        Task
            The task channel object.
        """

        task = "!" + task_name.lstrip("!")
        payload = {
            "msg": {},  # this is a required field apparently
            "processor_id": processor_id,
        }
        self.request(Route("POST", "/ch/v1/agent/{}/{}/", agent_id, task), json=payload)
        return self.get_channel_named(task, agent_id)

    def _maybe_subscribe_to_channel(
        self, channel_id: str, task_id: str, subscribe: bool
    ):
        data = {"channel_id": channel_id, "subscribe": subscribe}
        return self.request(
            Route("POST", "/ch/v1/channel/{}/subscribe/", task_id), json=data
        )

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
        # basically we're assuming there's only 2 types of data - dict or string...
        post_data = {"msg": data}

        post_data["record_log"] = save_log
        if log_aggregate:
            post_data["log_aggregate"] = True
        if override_aggregate:
            post_data["override_aggregate"] = True
        if timestamp:
            post_data["timestamp"] = int(timestamp.timestamp())

        if isinstance(post_data, dict):
            return self.request(
                Route("POST", "/ch/v1/channel/{}/", channel_id), json=post_data
            )
        else:
            return self.request(
                Route("POST", "/ch/v1/channel/{}/", channel_id), data=str(post_data)
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
        post_data = {"msg": data}

        post_data["record_log"] = save_log
        if log_aggregate:
            post_data["log_aggregate"] = True
        if override_aggregate:
            post_data["override_aggregate"] = True
        if timestamp:
            post_data["timestamp"] = int(timestamp.timestamp())

        if isinstance(post_data, dict):
            return self.request(
                Route("POST", "/ch/v1/agent/{}/{}/", agent_id, channel_name),
                json=post_data,
            )
        else:
            return self.request(
                Route("POST", "/ch/v1/agent/{}/{}/", agent_id, channel_name),
                data=str(post_data),
            )

    def create_tunnel_endpoints(self, agent_id: str, endpoint_type: str, amount: int):
        to_return = []
        for i in range(amount):
            res = self.request(
                Route(
                    "POST", "/ch/v1/agent/{}/ngrok_tunnels/{}/", agent_id, endpoint_type
                )
            )
            if res and res.get("url"):
                to_return.append(res["url"])
        return to_return

    def get_tunnel_endpoints(self, agent_id: str, endpoint_type: str):
        return self.request(
            Route("GET", "/ch/v1/agent/{}/ngrok_tunnels/{}/", agent_id, endpoint_type)
        )

    def get_tunnel(self, tunnel_id: str):
        return self.request(Route("GET", "/ch/v1/tunnels/{}/", tunnel_id))

    def get_tunnels(self, agent_id: str, show_choices: bool = False):
        return self.request(
            Route("GET", "/ch/v1/agent/{}/dd_tunnels/", agent_id, choices=show_choices)
        )

    def create_tunnel(self, agent_id: str, **data):
        return self.request(
            Route("POST", "/ch/v1/agent/{}/dd_tunnels/", agent_id), json=data
        )

    def patch_tunnel(self, tunnel_id: str, **data):
        return self.request(Route("PATCH", "/ch/v1/tunnels/{}/", tunnel_id), json=data)

    def activate_tunnel(self, tunnel_id: str):
        return self.request(Route("POST", "/ch/v1/tunnels/{}/activate/", tunnel_id))

    def deactivate_tunnel(self, tunnel_id: str):
        return self.request(Route("POST", "/ch/v1/tunnels/{}/deactivate/", tunnel_id))

    def delete_tunnel(self, tunnel_id: str):
        return self.request(Route("DELETE", "/ch/v1/tunnels/{}/", tunnel_id))

    # applications. only supports operations on apps, not installs / deployments at the moment.
    def get_applications(self):
        """Get the list of applications available to the current agent."""
        return self.request(Route("GET", "/apps/api/v1/applications/"))

    def create_application(self, application: Application) -> str:
        """Create a new application with the given data."""
        payload = application.to_dict(include_deployment_data=True)
        del payload["image_name"]  # not supported by site yet.
        data = self.request(Route("POST", "/apps/api/v1/applications/"), json=payload)
        return data["key"]

    def get_application(self, key: str) -> Application:
        """Get a specific application by its key."""
        data = self.request(Route("GET", "/apps/api/v1/applications/{}/", key))
        return Application.from_data(data=data)

    def update_application(self, application: Application) -> None:
        """Update an existing application with the given data."""
        payload = application.to_dict(include_deployment_data=True)
        del payload["image_name"]  # not supported by site yet.
        return self.request(
            Route("PATCH", "/apps/api/v1/applications/{}/", application.key),
            json=payload,
        )

    # login methods

    def fetch_token(self):
        """Fetch a temporary token from the cloud API.

        By default, this uses the username and password set in the client, and will fail if this is not set.

        You can override this to implement a custom token refresher, e.g. using the device agent websocket connection.

        This must return a tuple of (token, expires_at, agent_id).
        """
        if not (self.username or self.password):
            raise RuntimeError(
                "Must have username and password set since access token has expired."
            )

        logging.info("Logging in...")
        session = requests.Session()

        login_url = f"{self.base_url}/accounts/login/"

        session.get(login_url)
        login_data = dict(
            login=self.username,
            password=self.password,
            csrfmiddlewaretoken=session.cookies.get("csrftoken"),
            next="/",
        )
        res = session.post(login_url, data=login_data, headers=dict(Referer=login_url))

        # bit of a hack... don't know a better way? Two-Factor is the title on the page...
        if "Two-Factor" in res.text:
            print(
                "Your account has 2FA enabled. It is recommended to instead use `doover configure_token` "
                "and use a long-lived token, otherwise you will have to 2FA authenticate every 20min.\n"
                "Quit and run that command, or supply your 2FA code to authenticate now.\n"
            )

            token = input("Please enter your 2FA token: ")
            twofa_data = dict(
                csrfmiddlewaretoken=session.cookies.get("csrftoken"),
                code=token,
            )
            twofa_url = f"{self.base_url}/accounts/2fa/authenticate/"
            res = session.post(
                twofa_url, data=twofa_data, headers=dict(Referer=twofa_url)
            )
            if res.status_code != 200:
                raise RuntimeError("Failed to authenticate 2FA.")

        res = session.get(f"{self.base_url}/ch/v1/get_temp_token/")

        try:
            data = res.json()
        except requests.exceptions.JSONDecodeError:
            raise RuntimeError("Failed to get temporary token. Login failed.")

        # FIXME: can these expire in UTC?
        difference = timedelta(
            seconds=float(data["valid_until"]) - float(data["current_time"])
        )
        expires_at = datetime.utcnow() + difference
        return data["token"], expires_at, data["agent_id"]

    def login(self):
        token, expires_at, agent_id = self.fetch_token()
        self._set_login_data(token, expires_at, agent_id)

    def _set_login_data(self, token, expires_at, agent_id):
        self.access_token = AccessToken(token=token, expires_at=expires_at)
        self.agent_id = agent_id
        self.update_headers()

        logging.info(
            f"Successfully logged in and set token to expire "
            f"in {int((expires_at - datetime.utcnow()).total_seconds() / 60)}min..."
        )
        try:
            self.login_callback()
        except Exception as e:
            print(f"failed to call callback: {e}")
            pass
