import logging

from collections import namedtuple
from datetime import datetime
from typing import Callable
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
        *,
        refresh_token: str = None,
        refresh_token_id: str = None,
        data_base_url: str = "https://data.doover.com/api",
        auth_server_url: str = "https://auth.doover.com",
        auth_server_client_id: str = None,
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
                refresh_token = config.refresh_token
                refresh_token_id = config.refresh_token_id
                data_base_url = config.base_data_url
                auth_server_url = config.auth_server_url
                auth_server_client_id = config.auth_server_client_id
            else:
                username = config.username
                password = config.password
                token = config.token
                token_expires = config.token_expires
                base_url = config.base_url
                agent_id = config.agent_id

            self.is_doover2 = config.is_doover2

        access_token = AccessToken(token, token_expires)
        if is_doover2:
            refresh_token = RefreshToken(refresh_token, refresh_token_id)
            # cyclic imports
            from .client_v2 import Client as ClientV2

            self.client = ClientV2(
                access_token,
                refresh_token,
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
