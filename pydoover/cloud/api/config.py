"""CLI Config"""

import base64
import os
import re

from datetime import datetime, timezone


class NotSet:
    pass


class ConfigEntry:
    pattern = re.compile(
        r".*\[profile=(?P<profile>.+)]\n"
        r"USERNAME=(?P<username>.*)\n"
        r"PASSWORD=(?P<password>.*)\n"
        r"TOKEN=(?P<token>.*)\n"
        r"TOKEN_EXPIRES=(?P<token_expires>.*)\n"
        r"AGENT_ID=(?P<agent_id>.*)\n"
        r"BASE_URL=(?P<base_url>.*)(\n?)"
        r"(?:IS_DOOVER2=(?P<is_doover2>.*)\n)?"
        r"(?:REFRESH_TOKEN=(?P<refresh_token>.*)\n)?"
        r"(?:REFRESH_TOKEN_ID=(?P<refresh_token_id>.*)\n)?"
        r"(?:BASE_DATA_URL=(?P<base_data_url>.*)\n)?"
        r"(?:AUTH_SERVER_URL=(?P<auth_server_url>.*)\n)?"
        r"(?:AUTH_SERVER_CLIENT_ID=(?P<auth_server_client_id>.*)(\n?))?"
    )

    def __init__(
        self,
        profile: str,
        username: str = None,
        password: str = None,
        token: str = None,
        token_expires: datetime = None,
        agent_id: str = None,
        base_url: str = None,
        is_doover2: bool = None,
        refresh_token: str = None,
        refresh_token_id: str = None,
        base_data_url: str = None,
        auth_server_url: str = None,
        auth_server_client_id: str = None,
    ):
        self.profile = profile

        self.username = username or None
        self.password = password or None

        self.token = token or None
        self.token_expires = token_expires or None

        self.is_doover2 = is_doover2 or False
        self.refresh_token = refresh_token
        self.refresh_token_id = refresh_token_id
        self.base_data_url = base_data_url
        self.auth_server_url = auth_server_url
        self.auth_server_client_id = auth_server_client_id

        self.agent_id = agent_id or None
        self.base_url = base_url or None

        self.valid = True

    def __repr__(self):
        return f"ConfigEntry <profile={self.profile}, username={self.username}, base_url={self.base_url}>"

    @classmethod
    def from_data(cls, data):
        match = cls.pattern.match(data.strip())

        if match["token_expires"]:
            token_expires = datetime.fromtimestamp(
                float(match["token_expires"]), tz=timezone.utc
            )
        else:
            token_expires = None

        return cls(
            match["profile"],
            match["username"],
            base64.b64decode(match["password"]).decode("utf-8"),
            match["token"],
            token_expires,
            match["agent_id"],
            match["base_url"],
            True if match["is_doover2"] == "True" else False,
            match["refresh_token"],
            match["refresh_token_id"],
            match["base_data_url"],
            match["auth_server_url"],
            match["auth_server_client_id"],
        )

    def format(self):
        password = self.password or ""
        return (
            f"[profile={self.profile or ''}]\n"
            f"USERNAME={self.username or ''}\n"
            f"PASSWORD={base64.b64encode(password.encode('utf-8')).decode('utf-8') or ''}\n"
            f"TOKEN={self.token or ''}\n"
            f"TOKEN_EXPIRES={self.token_expires and self.token_expires.timestamp() or ''}\n"
            f"AGENT_ID={self.agent_id or ''}\n"
            f"BASE_URL={self.base_url or ''}\n"
            f"IS_DOOVER2={self.is_doover2}\n"
            f"REFRESH_TOKEN={self.refresh_token or ''}\n"
            f"REFRESH_TOKEN_ID={self.refresh_token_id or ''}\n"
            f"BASE_DATA_URL={self.base_data_url or ''}\n"
            f"AUTH_SERVER_URL={self.auth_server_url or ''}\n"
            f"AUTH_SERVER_CLIENT_ID={self.auth_server_client_id or ''}\n"
        )


class ConfigManager:
    directory = os.path.expanduser("~/.doover")
    filepath = os.path.join(directory, "config")

    def __init__(self, current_profile: str = None):
        self.entries = {}
        self.current_profile = current_profile
        self.read()

    @property
    def current(self) -> ConfigEntry:
        return self.entries.get(self.current_profile)

    def create(self, entry: ConfigEntry):
        self.entries[entry.profile] = entry

    def read(self):
        if not os.path.exists(self.filepath):
            return
            # self.parser.error("Config file doesn't exist. Please run `pydoover configure`.")

        with open(self.filepath, "r") as fp:
            contents = fp.read()

        if len(contents) == 0:
            # protect against empty file
            return

        self.parse(contents)

    def parse(self, contents):
        for item in contents.split("\n\n"):
            config = ConfigEntry.from_data(item)
            self.entries[config.profile] = config

    def write(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        fmt = self.dump()  # do this here, so we don't write in case something breaks in formatting config
        with open(self.filepath, "w") as fp:
            fp.write(fmt)

    def dump(self):
        return "\n\n".join(e.format() for e in self.entries.values())
