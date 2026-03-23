"""Backward-compatible config exports for cloud.api.

The underlying config implementation now lives under ``pydoover.api.auth`` and
only manages Doover 2-style auth profiles. This module keeps the historical
``ConfigEntry`` / ``ConfigManager`` import path working for callers that still
use ``pydoover.cloud.api``.
"""

from __future__ import annotations

import base64
import re
from datetime import datetime, timezone

from ...api.auth import AuthProfile


class ConfigEntry(AuthProfile):
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
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        token_expires: datetime | None = None,
        agent_id: str | None = None,
        base_url: str | None = None,
        is_doover2: bool | None = None,
        refresh_token: str | None = None,
        refresh_token_id: str | None = None,
        base_data_url: str | None = None,
        auth_server_url: str | None = None,
        auth_server_client_id: str | None = None,
    ):
        super().__init__(
            profile=profile,
            token=token,
            token_expires=token_expires,
            agent_id=agent_id,
            control_base_url=base_url,
            data_base_url=base_data_url,
            refresh_token=refresh_token,
            refresh_token_id=refresh_token_id,
            auth_server_url=auth_server_url,
            auth_server_client_id=auth_server_client_id,
        )
        self.username = username or None
        self.password = password or None
        self._is_doover2 = True if is_doover2 is None else bool(is_doover2)
        self.valid = True

    def __repr__(self):
        return f"ConfigEntry <profile={self.profile}, username={self.username}, base_url={self.base_url}>"

    @classmethod
    def from_data(cls, data: str) -> "ConfigEntry":
        match = cls.pattern.match(data.strip())
        if match is None:
            raise ValueError("Invalid config entry format")

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
        return (
            "ConfigEntry "
            f"<profile={self.profile}, username={self.username}, base_url={self.base_url}>"
        )

    @property
    def is_doover2(self) -> bool:
        return self._is_doover2
