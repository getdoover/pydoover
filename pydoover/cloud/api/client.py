import logging

from collections import namedtuple
from datetime import datetime
from typing import Any, Callable
from urllib.parse import quote, urlencode


from .config import ConfigManager


log = logging.getLogger(__name__)
AccessToken = namedtuple("AccessToken", ["token", "expires_at"], defaults=(None,))
RefreshToken = namedtuple("RefreshToken", ["token", "token_id"], defaults=(None, None))


class Route:
    def __init__(self, method, route, *args, **kwargs):
        self.method = method

        self.url = route
        if args:
            self.url = route.format(*[quote(str(a)) for a in args])

        if kwargs:
            self.url = f"{self.url}?{urlencode(kwargs)}"


class Client:
    """API Client for Doover Cloud

    This probably looks a bit dumb, it is a bit dumb, but it provides interoperability between Doover 1.0 and Doover 2.0
    clients without making breaking changes, in a way which makes it easy to develop each client independently.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        token_expires: datetime | None = None,
        base_url: str = "https://my.doover.dev",
        agent_id: str | None = None,
        verify: bool = True,
        login_callback: Callable[..., Any] | None = None,
        config_profile: str = "default",
        debug: bool = False,
        *,
        refresh_token: str | None = None,
        refresh_token_id: str | None = None,
        data_base_url: str = "https://data.doover.com/api",
        auth_server_url: str = "https://auth.doover.com",
        auth_server_client_id: str | None = None,
        is_doover2: bool = False,
    ):
        self.is_doover2 = is_doover2

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

            if config.is_doover2:
                refresh_token = config.refresh_token or refresh_token
                refresh_token_id = config.refresh_token_id or refresh_token_id
                data_base_url = config.base_data_url or data_base_url
                auth_server_url = config.auth_server_url or auth_server_url
                auth_server_client_id = (
                    config.auth_server_client_id or auth_server_client_id
                )
                base_url = config.base_url or base_url
            else:
                username = config.username or username
                password = config.password or password
                token = config.token or token
                token_expires = config.token_expires or token_expires
                base_url = config.base_url or base_url
                agent_id = config.agent_id or agent_id

            self.is_doover2 = config.is_doover2

        access_token = AccessToken(token, token_expires)
        if self.is_doover2:
            refresh_token_pair = RefreshToken(refresh_token, refresh_token_id)
            # cyclic imports
            from .client_v2 import Client as ClientV2

            self.client = ClientV2(
                access_token,
                refresh_token_pair,
                base_url,
                data_base_url,
                auth_server_url,
                auth_server_client_id,
                verify,
                login_callback,
            )
        else:
            from .client_v1 import Client as ClientV1

            self.client = ClientV1(
                username,
                password,
                token,
                token_expires,
                base_url,
                agent_id,
                verify,
                login_callback,
                config_profile,
            )

    def __getattr__(self, item):
        return getattr(self.client, item)

    def has_persistent_connection(self):
        return False
