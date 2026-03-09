from __future__ import annotations

from typing import Any


class TagsManager:
    """Base interface for manager-backed tag access."""

    def get_tag(
        self, key: str, default: Any = None, app_key: str | None = None
    ) -> Any | None:
        raise NotImplementedError

    def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
        raise NotImplementedError

    async def finalise_tags(self) -> None:
        return


class TagsManagerDocker(TagsManager):
    def __init__(self, app):
        self.app = app

    def get_tag(
        self, key: str, default: Any = None, app_key: str | None = None
    ) -> Any | None:
        return self.app.get_tag(key, app_key=app_key, default=default)

    def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
        self.app.set_tag(key, value, app_key=app_key)


class TagsManagerProcessor(TagsManager):
    def __init__(
        self,
        app_key: str,
        client,
        agent_id: int,
        tag_values: dict[str, Any] | None,
        record_tag_update: bool = True,
    ):
        self.client = client
        self.app_key = app_key
        self.agent_id = agent_id
        self._tag_values = tag_values or {}
        self._update_tags = False
        self._record_tag_update = record_tag_update

    def get_tag(
        self, key: str, default: Any = None, app_key: str | None = None
    ) -> Any | None:
        app_key = app_key or self.app_key
        try:
            return self._tag_values[app_key][key]
        except (KeyError, TypeError):
            return default

    def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
        app_key = app_key or self.app_key

        try:
            current = self._tag_values[app_key][key]
        except (KeyError, TypeError):
            current = None

        if current == value:
            return

        try:
            self._tag_values[app_key][key] = value
        except KeyError:
            self._tag_values[app_key] = {key: value}

        self._update_tags = True

    async def finalise_tags(self) -> None:
        if not self._update_tags:
            return

        await self.client.update_aggregate(
            self.agent_id,
            "tag_values",
            self._tag_values,
        )

        if self._record_tag_update:
            await self.client.publish_message(
                self.agent_id,
                "tag_values",
                self._tag_values,
            )

        self._update_tags = False
