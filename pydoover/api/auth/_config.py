from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from ._base import AuthProfile

_PROFILE_HEADER_RE = re.compile(r"^\[profile=(?P<profile>.+)]$")
_BLOCK_SPLIT_RE = re.compile(r"(?:\r?\n){2,}")


class ConfigManager:
    directory = os.path.expanduser("~/.doover")
    filepath = os.path.join(directory, "config")

    def __init__(self, current_profile: str | None = None):
        self.entries: dict[str, AuthProfile] = {}
        self.current_profile = current_profile
        self._blocks: list[tuple[str, str]] = []
        self.read()

    @property
    def current(self) -> AuthProfile | None:
        if self.current_profile is None:
            return None
        return self.entries.get(self.current_profile)

    def get(self, profile_name: str) -> AuthProfile | None:
        return self.entries.get(profile_name)

    def create(self, entry: AuthProfile):
        self.entries[entry.profile] = entry
        if not any(kind == "managed" and value == entry.profile for kind, value in self._blocks):
            self._blocks.append(("managed", entry.profile))

    def delete(self, profile_name: str):
        self.entries.pop(profile_name, None)
        self._blocks = [
            (kind, value)
            for kind, value in self._blocks
            if not (kind == "managed" and value == profile_name)
        ]

    def read(self):
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath, "r", encoding="utf-8") as fp:
            contents = fp.read()

        if not contents:
            return

        self.parse(contents)

    def parse(self, contents: str):
        self.entries = {}
        self._blocks = []

        for raw_block in _BLOCK_SPLIT_RE.split(contents):
            if not raw_block.strip():
                continue
            parsed = self._parse_block(raw_block)
            if isinstance(parsed, AuthProfile):
                self.entries[parsed.profile] = parsed
                self._blocks.append(("managed", parsed.profile))
            else:
                self._blocks.append(("raw", parsed))

    def write(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        with open(self.filepath, "w", encoding="utf-8") as fp:
            fp.write(self.dump())

    def dump(self) -> str:
        blocks: list[str] = []
        written: set[str] = set()

        for kind, value in self._blocks:
            if kind == "raw":
                blocks.append(value)
                continue

            if value in written:
                continue
            entry = self.entries.get(value)
            if entry is None:
                continue
            blocks.append(entry.format())
            written.add(value)

        for profile_name, entry in self.entries.items():
            if profile_name in written:
                continue
            blocks.append(entry.format())

        return "\n\n".join(blocks)

    def _parse_block(self, raw_block: str) -> AuthProfile | str:
        lines = raw_block.splitlines()
        if not lines:
            return raw_block

        header = _PROFILE_HEADER_RE.match(lines[0].strip())
        if not header:
            return raw_block

        fields: dict[str, str] = {}
        for line in lines[1:]:
            if "=" not in line:
                return raw_block
            key, value = line.split("=", 1)
            fields[key] = value

        is_doover2 = fields.get("IS_DOOVER2") == "True"
        has_legacy_credentials = "USERNAME" in fields or "PASSWORD" in fields
        if has_legacy_credentials and not is_doover2:
            return raw_block

        token_expires_raw = fields.get("TOKEN_EXPIRES") or None
        token_expires = None
        if token_expires_raw:
            token_expires = datetime.fromtimestamp(
                float(token_expires_raw), tz=timezone.utc
            )

        return AuthProfile(
            profile=header.group("profile"),
            token=fields.get("TOKEN") or None,
            token_expires=token_expires,
            agent_id=fields.get("AGENT_ID") or None,
            control_base_url=fields.get("BASE_URL") or None,
            data_base_url=fields.get("BASE_DATA_URL") or None,
            refresh_token=fields.get("REFRESH_TOKEN") or None,
            refresh_token_id=fields.get("REFRESH_TOKEN_ID") or None,
            auth_server_url=fields.get("AUTH_SERVER_URL") or None,
            auth_server_client_id=fields.get("AUTH_SERVER_CLIENT_ID") or None,
        )
