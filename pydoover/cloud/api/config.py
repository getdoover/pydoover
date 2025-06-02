"""CLI Config"""

import base64
import os
import re

from datetime import datetime


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
        r"BASE_URL=(?P<base_url>.*)"
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
    ):
        self.profile = profile

        self.username = username or None
        self.password = password or None

        self.token = token or None
        self.token_expires = token_expires or None

        self.agent_id = agent_id or None
        self.base_url = base_url or None

        self.valid = True

    def __repr__(self):
        return f"ConfigEntry <profile={self.profile}, username={self.username}, base_url={self.base_url}>"

    @classmethod
    def from_data(cls, data):
        match = cls.pattern.match(data.strip())

        if match["token_expires"]:
            token_expires = datetime.fromtimestamp(float(match["token_expires"]))
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
