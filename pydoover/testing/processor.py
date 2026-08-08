from __future__ import annotations

import base64
import copy
import inspect
import importlib
import io
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydoover.models.data import Aggregate, Channel, ChannelID, Message
from pydoover.processor import Application
from pydoover.processor.data_client import ProcessorDataClient


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _coerce_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _timestamp_to_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
    if isinstance(value, str):
        parsed = value.replace("Z", "+00:00")
        return datetime.fromisoformat(parsed)
    return None


def _aggregate_from_snapshot(payload: dict[str, Any]) -> Aggregate:
    timestamp = _first_present(payload.get("last_updated"), payload.get("timestamp"))
    return Aggregate(
        payload.get("data") or {},
        payload.get("attachments") or [],
        _timestamp_to_datetime(timestamp),
    )


def _serializable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict"):
        return _serializable(value.to_dict())
    return value


def env_data_client_allows_missing(env: "ProcessorTestEnvironment | None") -> bool:
    return bool(env and env.data_client and env.data_client.delegate_missing_reads)


@dataclass
class ProcessorInvocationEvent:
    payload: dict[str, Any]
    refresh: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.payload

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]


@dataclass
class ProcessorSnapshot:
    agent_id: int | None = None
    organisation_id: int | None = None
    app_key: str | None = None
    app_id: int | None = None
    app_install_id: int | None = None
    token: str = "test-processor-token"
    deployment_config: dict[str, Any] = field(default_factory=dict)
    tag_values: dict[str, Any] = field(default_factory=dict)
    ui_state: dict[str, Any] = field(default_factory=dict)
    ui_cmds: dict[str, Any] = field(default_factory=dict)
    connection_data: dict[str, Any] = field(default_factory=dict)
    channels: dict[str, Channel] = field(default_factory=dict)
    messages: dict[str, list[Message]] = field(default_factory=dict)

    def __post_init__(self):
        self.processor_info = SimpleNamespace(
            deployment_config=self.deployment_config,
            tag_values=self.tag_values,
            ui_state=self.ui_state,
            ui_cmds=self.ui_cmds,
            connection_data=self.connection_data,
            token=self.token,
        )

    def to_upgrade_payload(self) -> dict[str, Any]:
        app_key = self.app_key or "app"
        deployment_config = {
            "APP_ID": str(self.app_id or self.app_install_id or app_key),
            "APP_DISPLAY_NAME": app_key,
            "dv_proc_config": {"inv_targets": []},
            **self.deployment_config,
        }
        return {
            "agent_id": self.agent_id or 0,
            "organisation_id": self.organisation_id or 0,
            "app_key": app_key,
            "app_id": self.app_id,
            "app_install_id": self.app_install_id,
            "deployment_config": deployment_config,
            "ui_state": self.ui_state,
            "ui_cmds": self.ui_cmds,
            "tag_values": self.tag_values,
            "connection_data": self.connection_data,
            "token": self.token,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessorSnapshot":
        app = data.get("app") or {}
        owner = data.get("owner") or {}
        processor_info = data.get("processor_info") or {}
        channels = cls._channels_from_snapshot(data.get("channels", {}))
        messages = cls._messages_from_snapshot(data.get("messages", {}))
        return cls(
            agent_id=_coerce_int(
                _first_present(
                    data.get("agent_id"),
                    owner.get("agent_id"),
                    processor_info.get("agent_id"),
                )
            ),
            organisation_id=_coerce_int(
                _first_present(
                    data.get("organisation_id"),
                    owner.get("organisation_id"),
                    processor_info.get("organisation_id"),
                )
            ),
            app_key=_first_present(
                data.get("app_key"),
                app.get("app_key"),
                app.get("key"),
                app.get("local_name"),
                processor_info.get("app_key"),
            ),
            app_id=_coerce_int(_first_present(data.get("app_id"), app.get("app_id"))),
            app_install_id=_coerce_int(
                _first_present(
                    data.get("app_install_id"),
                    app.get("app_install_id"),
                    app.get("install_id"),
                )
            ),
            token=_first_present(
                data.get("token"), processor_info.get("token"), "test-processor-token"
            ),
            deployment_config=_coerce_dict(
                _first_present(
                    processor_info.get("deployment_config"),
                    data.get("deployment_config"),
                    app.get("deployment_config"),
                    {},
                )
            ),
            tag_values=_coerce_dict(
                _first_present(
                    processor_info.get("tag_values"),
                    data.get("tag_values"),
                    {},
                )
            ),
            ui_state=_coerce_dict(
                _first_present(
                    processor_info.get("ui_state"),
                    data.get("ui_state"),
                    {},
                )
            ),
            ui_cmds=_coerce_dict(
                _first_present(
                    processor_info.get("ui_cmds"),
                    data.get("ui_cmds"),
                    {},
                )
            ),
            connection_data=_coerce_dict(
                _first_present(
                    processor_info.get("connection_data"),
                    data.get("connection_data"),
                    {},
                )
            ),
            channels=channels,
            messages=messages,
        )

    @classmethod
    def _channels_from_snapshot(cls, payload: Any) -> dict[str, Channel]:
        if isinstance(payload, list):
            items = [
                (item.get("name") or (item.get("id") or {}).get("name"), item)
                for item in payload
                if isinstance(item, dict)
            ]
        elif isinstance(payload, dict):
            items = payload.items()
        else:
            return {}

        return {
            name: cls._channel_from_snapshot(name, item)
            for name, item in items
            if name and isinstance(item, dict)
        }

    @staticmethod
    def _messages_from_snapshot(payload: Any) -> dict[str, list[Message]]:
        if not isinstance(payload, dict):
            return {}
        return {
            name: [Message.from_dict(item) for item in items if isinstance(item, dict)]
            for name, items in payload.items()
            if isinstance(items, list)
        }

    @staticmethod
    def _channel_from_snapshot(name: str, payload: dict[str, Any]) -> Channel:
        channel_id = payload.get("id") or {}
        channel_name = payload.get("name") or channel_id.get("name") or name
        aggregate = _aggregate_from_snapshot(payload.get("aggregate") or {"data": {}})
        return Channel(
            channel_name,
            _coerce_int(
                _first_present(
                    payload.get("owner_id"),
                    payload.get("agent_id"),
                    channel_id.get("agent_id"),
                    0,
                )
            )
            or 0,
            payload.get("is_private", False),
            payload.get("aggregate_schema"),
            payload.get("message_schema"),
            aggregate,
        )


@dataclass
class RecordedWrite:
    method: str
    agent_id: int | None = None
    organisation_id: int | None = None
    channel: str | None = None
    data: dict[str, Any] | None = None
    files: list[Any] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "agent_id": self.agent_id,
            "organisation_id": self.organisation_id,
            "channel": self.channel,
            "data": _serializable(self.data),
            "files": _serializable(self.files),
            "options": _serializable(self.options),
            "timestamp_ms": self.timestamp_ms,
        }


class RecordedWrites(list[RecordedWrite]):
    def to_dicts(self) -> list[dict[str, Any]]:
        return [write.to_dict() for write in self]


@dataclass
class ProcessorTestResult:
    status: str
    return_value: Any = None
    error: BaseException | None = None
    logs: list[logging.LogRecord] = field(default_factory=list)
    writes: RecordedWrites = field(default_factory=RecordedWrites)
    generated_files: list[Path] = field(default_factory=list)
    duration_ms: int = 0
    invocation: Any = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        invocation = (
            vars(self.invocation)
            if not isinstance(self.invocation, dict)
            else self.invocation
        )
        return {
            "status": self.status,
            "duration_ms": self.duration_ms,
            "writes": [write.to_dict() for write in self.writes],
            "generated_files": [str(path) for path in self.generated_files],
            "invocation": invocation,
            "error": str(self.error) if self.error else None,
        }


class ReadPolicy:
    def __init__(self, client: "SandboxProcessorDataClient"):
        self._client = client

    async def use_live_snapshot(self, **kwargs: Any) -> ProcessorSnapshot:
        channels = kwargs.get("channels") or []
        latest_messages = kwargs.get("latest_messages") or []
        if isinstance(latest_messages, dict):
            messages = {
                channel: [
                    Message(
                        item.get("id") or int(time.time() * 1000),
                        item.get("author_id") or kwargs.get("agent_id") or 0,
                        ChannelID(kwargs.get("agent_id") or 0, channel),
                        item.get("data") or {},
                        item.get("attachments") or [],
                    )
                ]
                for channel, item in latest_messages.items()
                if isinstance(item, dict)
            }
        else:
            messages = {
                channel: [
                    Message(
                        int(time.time() * 1000),
                        kwargs.get("agent_id") or 0,
                        ChannelID(kwargs.get("agent_id") or 0, channel),
                        {},
                        [],
                    )
                ]
                for channel in latest_messages
            }
        snapshot = ProcessorSnapshot(
            agent_id=kwargs.get("agent_id"),
            organisation_id=kwargs.get("organisation_id"),
            app_key=kwargs.get("app_key"),
            app_id=kwargs.get("app_id") or kwargs.get("app_install_id"),
            app_install_id=kwargs.get("app_install_id"),
            channels={
                channel: Channel(
                    channel,
                    kwargs.get("agent_id") or 0,
                    False,
                    None,
                    None,
                    Aggregate({}, [], None),
                )
                for channel in channels
                if channel
                not in {
                    "deployment_config",
                    "tag_values",
                    "ui_state",
                    "ui_cmds",
                }
            },
            messages=messages,
        )
        self._client.snapshot = snapshot
        return snapshot

    async def use_snapshot_file(self, path: str | Path) -> ProcessorSnapshot:
        snapshot_path = Path(path)
        if not snapshot_path.is_absolute() and self._client.base_dir is not None:
            snapshot_path = self._client.base_dir / snapshot_path
        with snapshot_path.open() as fh:
            snapshot = ProcessorSnapshot.from_dict(json.load(fh))
        self._client.snapshot = snapshot
        return snapshot

    def use_fixtures(
        self, snapshot: ProcessorSnapshot | None = None
    ) -> ProcessorSnapshot:
        self._client.snapshot = snapshot or ProcessorSnapshot()
        return self._client.snapshot

    def use_live(self) -> None:
        self._client.delegate_missing_reads = True

    def delegate_missing(self, enabled: bool) -> None:
        self._client.delegate_missing_reads = enabled


class WritePolicy:
    def __init__(self, client: "SandboxProcessorDataClient"):
        self._client = client

    def capture(self) -> None:
        self._client.write_policy = "record"

    def block(self) -> None:
        self._client.write_policy = "block"

    def allow(self, confirm: bool = False) -> None:
        if not confirm:
            raise ValueError("allow writes requires confirm=True")
        self._client.write_policy = "allow"

    @property
    def recorded(self) -> RecordedWrites:
        return self._client.recorded_writes

    def to_dicts(self) -> list[dict[str, Any]]:
        return self._client.recorded_writes.to_dicts()


class SandboxProcessorDataClient(ProcessorDataClient):
    def __init__(self):
        super().__init__("http://processor-test.invalid")
        self.snapshot = ProcessorSnapshot()
        self.reads = ReadPolicy(self)
        self.writes = WritePolicy(self)
        self.recorded_writes = RecordedWrites()
        self.write_policy = "record"
        self.delegate_missing_reads = False
        self.blocked_write_error: RuntimeError | None = None
        self.base_dir: Path | None = None

    async def setup(self):
        return None

    async def close(self):
        return None

    def set_token(self, token: str):
        self._test_token = token

    def _record_write(
        self,
        method: str,
        *,
        channel_name: str | None = None,
        data: dict[str, Any] | None = None,
        files: list[Any] | None = None,
        agent_id: int | None = None,
        organisation_id: int | None = None,
        **options: Any,
    ) -> RecordedWrite:
        if self.write_policy == "block":
            self.blocked_write_error = RuntimeError(
                f"Processor write blocked: {method}"
            )
            raise self.blocked_write_error
        if self.write_policy == "allow":
            raise RuntimeError(
                "Live write passthrough is not implemented in the sandbox client"
            )

        write = RecordedWrite(
            method=method,
            agent_id=agent_id or self.agent_id,
            organisation_id=organisation_id or self.organisation_id,
            channel=channel_name,
            data=data,
            files=files or [],
            options={
                key: value
                for key, value in options.items()
                if value not in (None, False, [], {})
            },
        )
        self.recorded_writes.append(write)
        return write

    async def fetch_subscription_info(self, subscription_id: str):
        from pydoover.models.data import SubscriptionInfo

        return SubscriptionInfo.from_dict(self.snapshot.to_upgrade_payload())

    async def fetch_schedule_info(self, schedule_id: str):
        return await self.fetch_subscription_info(str(schedule_id))

    async def fetch_channel(
        self, channel_name: str, *args: Any, **kwargs: Any
    ) -> Channel:
        if channel_name in self.snapshot.channels:
            return self.snapshot.channels[channel_name]
        if self.delegate_missing_reads:
            return Channel(
                channel_name,
                self.snapshot.agent_id or self.agent_id or 0,
                False,
                None,
                None,
                Aggregate({}, [], None),
            )
        raise KeyError(f"Missing snapshot channel: {channel_name}")

    async def fetch_channel_aggregate(
        self, channel_name: str, *args: Any, **kwargs: Any
    ) -> Aggregate:
        return (await self.fetch_channel(channel_name)).aggregate

    async def list_messages(
        self, channel_name: str, *args: Any, **kwargs: Any
    ) -> list[Message]:
        if channel_name in self.snapshot.messages:
            return self.snapshot.messages[channel_name]
        if self.delegate_missing_reads:
            return []
        raise KeyError(f"Missing snapshot messages for channel: {channel_name}")

    async def fetch_message(
        self,
        channel_name: str,
        message_id: int,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Message:
        messages = self.snapshot.messages.get(channel_name, [])
        for message in messages:
            if message.id == int(message_id):
                return message
        if self.delegate_missing_reads:
            return Message(
                int(message_id),
                agent_id or self.snapshot.agent_id or self.agent_id or 0,
                ChannelID(
                    agent_id or self.snapshot.agent_id or self.agent_id or 0,
                    channel_name,
                ),
                {},
                [],
            )
        raise KeyError(
            f"Missing snapshot message {message_id} for channel: {channel_name}"
        )

    async def create_channel(
        self,
        channel_name: str,
        is_private: bool = False,
        message_schema: dict | None = None,
        aggregate_schema: dict | None = None,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> int:
        self._record_write(
            "create_channel",
            channel_name=channel_name,
            data={
                "is_private": is_private,
                "message_schema": message_schema,
                "aggregate_schema": aggregate_schema,
            },
            agent_id=agent_id,
            organisation_id=organisation_id,
        )
        return int(time.time() * 1000)

    async def put_channel(
        self,
        channel_name: str,
        is_private: bool,
        message_schema: dict | None = None,
        aggregate_schema: dict | None = None,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Channel:
        self._record_write(
            "put_channel",
            channel_name=channel_name,
            data={
                "is_private": is_private,
                "message_schema": message_schema,
                "aggregate_schema": aggregate_schema,
            },
            agent_id=agent_id,
            organisation_id=organisation_id,
        )
        return Channel(
            channel_name,
            agent_id or self.agent_id or 0,
            is_private,
            aggregate_schema,
            message_schema,
            Aggregate({}, [], None),
        )

    async def create_message(
        self,
        channel_name: str,
        data: dict[str, Any],
        timestamp: int | None = None,
        files: list[Any] | None = None,
        allow_invoking_channel: bool = False,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Message:
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)
        self._record_write(
            "create_message",
            channel_name=channel_name,
            data=data,
            files=files,
            agent_id=agent_id,
            organisation_id=organisation_id,
            timestamp=timestamp,
            allow_invoking_channel=allow_invoking_channel,
        )
        return Message(
            timestamp or int(time.time() * 1000),
            agent_id or self.agent_id or 0,
            ChannelID(agent_id or self.agent_id or 0, channel_name),
            data,
            [],
        )

    async def update_channel_aggregate(
        self,
        channel_name: str,
        data: dict[str, Any],
        replace_data: bool = False,
        files: list[Any] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        log_update: bool = False,
        replace_keys: list[str] | None = None,
        allow_invoking_channel: bool = False,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Aggregate | None:
        if channel_name == self._invoking_channel_name:
            self._check_invoking_channel(channel_name, data, allow_invoking_channel)
        self._record_write(
            "update_channel_aggregate",
            channel_name=channel_name,
            data=data,
            files=files,
            agent_id=agent_id,
            organisation_id=organisation_id,
            replace_data=replace_data,
            suppress_response=suppress_response,
            clear_attachments=clear_attachments,
            log_update=log_update,
            replace_keys=replace_keys,
            allow_invoking_channel=allow_invoking_channel,
        )
        if suppress_response:
            return None
        return Aggregate(data, [], None)

    async def update_message(
        self,
        channel_name: str,
        message_id: int,
        data: dict[str, Any],
        replace_data: bool = False,
        files: list[Any] | None = None,
        suppress_response: bool = False,
        clear_attachments: bool = False,
        allow_invoking_channel: bool = False,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ) -> Message | None:
        self._record_write(
            "update_message",
            channel_name=channel_name,
            data=data,
            files=files,
            agent_id=agent_id,
            organisation_id=organisation_id,
            message_id=message_id,
            replace_data=replace_data,
            suppress_response=suppress_response,
            clear_attachments=clear_attachments,
            allow_invoking_channel=allow_invoking_channel,
        )
        if suppress_response:
            return None
        return Message(
            message_id,
            agent_id or self.agent_id or 0,
            ChannelID(agent_id or self.agent_id or 0, channel_name),
            data,
            [],
        )

    async def delete_message(
        self,
        channel_name: str,
        message_id: int,
        agent_id: int | None = None,
        organisation_id: int | None = None,
    ):
        self._record_write(
            "delete_message",
            channel_name=channel_name,
            agent_id=agent_id,
            organisation_id=organisation_id,
            message_id=message_id,
        )


class ProcessorEventBuilder:
    def __init__(self, test: "ProcessorTest"):
        self._test = test

    def _base(
        self,
        op: str,
        data: dict[str, Any],
        refresh: dict[str, Any] | None = None,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        return ProcessorInvocationEvent(
            {
                "op": op,
                "token": snapshot.token,
                "agent_id": snapshot.agent_id,
                "d": {
                    **data,
                    "upgrade": snapshot.to_upgrade_payload(),
                },
            },
            refresh or {},
        )

    async def message_create(
        self,
        *,
        channel: str,
        message: dict[str, Any] | None = None,
        message_source: str | None = None,
        agent_id: int | None = None,
        author_id: int | None = None,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        owner = agent_id or snapshot.agent_id or 0
        requires_latest = message is None and message_source == "latest"
        if requires_latest:
            messages = snapshot.messages.get(channel, [])
            if messages:
                return self._base(
                    "on_message_create",
                    {"message": messages[-1].to_dict()},
                    {
                        "message_source": "latest",
                        "channel": channel,
                        "message_channel_agent_id": agent_id is None,
                        "message_author_id": author_id is None,
                    },
                )
            message = {}
        return self._base(
            "on_message_create",
            {
                "message": {
                    "id": int(time.time() * 1000),
                    "author_id": author_id or owner,
                    "channel": {"agent_id": owner, "name": channel},
                    "data": message or {},
                    "attachments": [],
                }
            },
            {
                "message_source": message_source,
                "channel": channel,
                "require_latest": requires_latest,
                "message_channel_agent_id": agent_id is None,
                "message_author_id": author_id is None,
            },
        )

    async def aggregate_update(
        self,
        *,
        channel: str,
        aggregate: dict[str, Any] | None = None,
        request_data: dict[str, Any] | None = None,
        agent_id: int | None = None,
        author_id: int | None = None,
        organisation_id: int | None = None,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        owner = agent_id or snapshot.agent_id or 0
        return self._base(
            "on_aggregate_update",
            {
                "author_id": author_id or owner,
                "organisation_id": organisation_id or snapshot.organisation_id or 0,
                "channel": {"agent_id": owner, "name": channel},
                "aggregate": {
                    "data": aggregate or {},
                    "attachments": [],
                    "last_updated": None,
                },
                "request_data": {
                    "data": request_data or {},
                    "attachments": [],
                    "last_updated": None,
                },
            },
            {
                "channel": channel,
                "aggregate_from_snapshot": aggregate is None,
                "aggregate_channel_agent_id": agent_id is None,
                "aggregate_author_id": author_id is None,
                "aggregate_organisation_id": organisation_id is None,
            },
        )

    async def ingestion(
        self,
        *,
        body: dict[str, Any] | bytes | str | None = None,
        body_path: str | Path | None = None,
        content_type: str | None = "application/json",
        invocation_url: str | None = None,
        ingestion_id: int = 0,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        if body_path is not None:
            raw = Path(body_path).read_bytes()
        elif isinstance(body, bytes):
            raw = body
        elif isinstance(body, str):
            raw = body.encode()
        else:
            raw = json.dumps(body or {}).encode()
        return self._base(
            "on_ingestion_endpoint",
            {
                "ingestion_id": ingestion_id,
                "agent_id": snapshot.agent_id or 0,
                "organisation_id": snapshot.organisation_id or 0,
                "payload": base64.b64encode(raw).decode(),
                "invocation_url": invocation_url,
                "content_type": content_type,
            },
            {
                "ingestion_agent_id": True,
                "ingestion_organisation_id": True,
            },
        )

    async def deployment(
        self,
        *,
        agent_id: int | None = None,
        app_id: int | None = None,
        app_install_id: int | None = None,
        app_key: str | None = None,
        app_display_name: str | None = None,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        return self._base(
            "on_deployment",
            {
                "agent_id": agent_id or snapshot.agent_id or 0,
                "app_id": app_id or snapshot.app_id or snapshot.app_install_id or 0,
                "app_install_id": app_install_id or snapshot.app_install_id or 0,
                "app_key": app_key or snapshot.app_key or self._test.app_name,
                "app_display_name": app_display_name
                or snapshot.deployment_config.get(
                    "APP_DISPLAY_NAME",
                    self._test.app_name,
                ),
            },
            {
                "deployment_agent_id": agent_id is None,
                "deployment_app_id": app_id is None,
                "deployment_app_install_id": app_install_id is None,
                "deployment_app_key": app_key is None,
                "deployment_app_display_name": app_display_name is None,
            },
        )

    async def schedule(self, schedule_id: int = 0) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        return self._base(
            "on_schedule",
            {
                "schedule_id": schedule_id,
                "organisation_id": snapshot.organisation_id or 0,
            },
            {"schedule_organisation_id": True},
        )

    async def manual_invoke(
        self,
        payload: dict[str, Any] | None = None,
        organisation_id: int | None = None,
    ) -> ProcessorInvocationEvent:
        snapshot = self._test._current_snapshot()
        return self._base(
            "on_manual_invoke",
            {
                "organisation_id": organisation_id or snapshot.organisation_id or 0,
                "payload": payload or {},
            },
            {"manual_organisation_id": organisation_id is None},
        )


class FileHelpers:
    async def json(self, path: str | Path) -> Any:
        with Path(path).open() as fh:
            return json.load(fh)


class AuthHelpers:
    def cli_user_for_reads(self, profile: str | None = None):
        return SimpleNamespace(
            kind="cli_user_for_reads",
            profile=profile,
            purpose="reads",
            allow_writes=False,
        )

    def cli_user(self, profile: str | None = None):
        return SimpleNamespace(
            kind="cli_user",
            profile=profile,
            purpose="reads_writes",
            allow_writes=True,
        )


class ProcessorTestEnvironment:
    def __init__(self):
        self.data_client: SandboxProcessorDataClient | None = None
        self.auth = None
        self.files = SimpleNamespace(
            output_dir=lambda path: setattr(self, "output_dir", Path(path))
        )
        self.output_dir: Path | None = None
        self._test: ProcessorTest | None = None

    def __enter__(self):
        if self._test is None:
            raise RuntimeError(
                "Environment must be created from a ProcessorTest instance"
            )
        if self.data_client is None:
            self.data_client = SandboxProcessorDataClient()
        self._test._environment_stack.append(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        assert self._test is not None
        self._test._environment_stack.pop()
        return False


class ProcessorTest:
    def __init__(
        self,
        app_name: str,
        *,
        app_install: str | int | None = None,
        application: Application | type[Application] | None = None,
        entrypoint: str | None = None,
    ):
        self.app_name = app_name
        self.app_install = app_install
        self.application = application
        self.entrypoint = entrypoint
        self.events = ProcessorEventBuilder(self)
        self.files = FileHelpers()
        self.auth = AuthHelpers()
        self.processor = SimpleNamespace(DataClient=SandboxProcessorDataClient)
        self._environment_stack: list[ProcessorTestEnvironment] = []

    def Environment(self) -> ProcessorTestEnvironment:  # noqa: N802
        env = ProcessorTestEnvironment()
        env._test = self
        return env

    def _current_env(self) -> ProcessorTestEnvironment | None:
        return self._environment_stack[-1] if self._environment_stack else None

    def _current_snapshot(self) -> ProcessorSnapshot:
        env = self._current_env()
        if env and env.data_client:
            return env.data_client.snapshot
        return ProcessorSnapshot(app_key=self.app_name)

    def _load_application(self) -> Application:
        app = self.application
        if app is None and self.entrypoint is None:
            config_path = self._find_doover_config()
            if config_path is not None:
                with config_path.open() as fh:
                    config = json.load(fh)
                entry = config.get(self.app_name) or {}
                self.entrypoint = entry.get("entrypoint") or (
                    entry.get("lambda_config") or {}
                ).get("Handler")
        if app is None and self.entrypoint:
            module_name, _, attr = self.entrypoint.partition(":")
            if not attr:
                module_name, _, attr = self.entrypoint.rpartition(".")
            if "" not in sys.path:
                sys.path.insert(0, "")
            src_path = Path.cwd() / "src"
            if src_path.exists() and str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            module = importlib.import_module(module_name)
            app = getattr(module, attr)
            if callable(app) and not isinstance(app, type):
                module_app = self._application_class_from_module(module)
                if module_app is not None:
                    app = module_app
        if isinstance(app, type):
            return app()
        if isinstance(app, Application):
            return app
        if callable(app):
            loaded = app()
            if isinstance(loaded, Application):
                return loaded
        raise RuntimeError(
            "ProcessorTest requires application= or entrypoint= to run locally"
        )

    @staticmethod
    def _application_class_from_module(module) -> type[Application] | None:
        candidates = [
            value
            for value in vars(module).values()
            if inspect.isclass(value)
            and issubclass(value, Application)
            and value is not Application
        ]
        if len(candidates) == 1:
            return candidates[0]
        return None

    @staticmethod
    def _find_doover_config() -> Path | None:
        current = Path.cwd().resolve()
        for path in (current, *current.parents):
            candidate = path / "doover_config.json"
            if candidate.exists():
                return candidate
        return None

    def _refresh_event_snapshot(
        self, event: dict[str, Any] | ProcessorInvocationEvent
    ) -> dict[str, Any]:
        if isinstance(event, ProcessorInvocationEvent):
            payload = copy.deepcopy(event.payload)
            refresh = event.refresh
        else:
            payload = copy.deepcopy(dict(event))
            refresh = {}

        snapshot = self._current_snapshot()
        agent_id = snapshot.agent_id or 0
        organisation_id = snapshot.organisation_id or 0
        d = payload.setdefault("d", {})

        d["upgrade"] = snapshot.to_upgrade_payload()
        payload["token"] = snapshot.token
        payload["agent_id"] = agent_id

        match payload.get("op"):
            case "on_message_create":
                message = d.setdefault("message", {})
                channel_name = refresh.get("channel") or (
                    message.get("channel") or {}
                ).get("name")
                used_latest = False
                if (
                    refresh.get("message_source") == "latest"
                    and channel_name in snapshot.messages
                    and snapshot.messages[channel_name]
                ):
                    message = d["message"] = snapshot.messages[channel_name][
                        -1
                    ].to_dict()
                    used_latest = True
                elif refresh.get(
                    "require_latest"
                ) and not env_data_client_allows_missing(self._current_env()):
                    raise KeyError(
                        f"Missing latest snapshot message for channel: {channel_name}"
                    )
                if refresh.get("message_channel_agent_id") and not used_latest:
                    message.setdefault("channel", {})["agent_id"] = agent_id
                if refresh.get("message_author_id") and not used_latest:
                    message["author_id"] = agent_id
            case "on_aggregate_update":
                channel_name = refresh.get("channel") or (d.get("channel") or {}).get(
                    "name"
                )
                if refresh.get("aggregate_channel_agent_id"):
                    d.setdefault("channel", {})["agent_id"] = agent_id
                if refresh.get("aggregate_author_id"):
                    d["author_id"] = agent_id
                if refresh.get("aggregate_organisation_id"):
                    d["organisation_id"] = organisation_id
                if (
                    refresh.get("aggregate_from_snapshot")
                    and channel_name in snapshot.channels
                ):
                    aggregate = snapshot.channels[channel_name].aggregate
                    if aggregate is not None:
                        d["aggregate"] = aggregate.to_dict()
                elif refresh.get(
                    "aggregate_from_snapshot"
                ) and not env_data_client_allows_missing(self._current_env()):
                    raise KeyError(
                        f"Missing snapshot aggregate for channel: {channel_name}"
                    )
            case "on_ingestion_endpoint":
                if refresh.get("ingestion_agent_id"):
                    d["agent_id"] = agent_id
                if refresh.get("ingestion_organisation_id"):
                    d["organisation_id"] = organisation_id
            case "on_deployment":
                if refresh.get("deployment_agent_id"):
                    d["agent_id"] = agent_id
                if refresh.get("deployment_app_id"):
                    d["app_id"] = snapshot.app_id or snapshot.app_install_id or 0
                if refresh.get("deployment_app_install_id"):
                    d["app_install_id"] = snapshot.app_install_id or 0
                if refresh.get("deployment_app_key"):
                    d["app_key"] = snapshot.app_key or self.app_name
                if refresh.get("deployment_app_display_name"):
                    d["app_display_name"] = snapshot.deployment_config.get(
                        "APP_DISPLAY_NAME",
                        snapshot.app_key or self.app_name,
                    )
                d["organisation_id"] = organisation_id
            case "on_schedule":
                if refresh.get("schedule_organisation_id"):
                    d["organisation_id"] = organisation_id
            case "on_manual_invoke":
                if refresh.get("manual_organisation_id"):
                    d["organisation_id"] = organisation_id

        return payload

    async def run(
        self, event: dict[str, Any] | ProcessorInvocationEvent
    ) -> ProcessorTestResult:
        started = time.perf_counter()
        env = self._current_env()
        if env is None:
            env = self.Environment()
            env.__enter__()
            close_env = True
        else:
            close_env = False

        if env.data_client is None:
            env.data_client = SandboxProcessorDataClient()

        app = self._load_application()
        if not hasattr(app, "log_capture_string"):
            app.log_capture_string = io.StringIO()
        app.api = env.data_client
        invocation_snapshot = self._current_snapshot()
        app.agent_id = invocation_snapshot.agent_id or app.agent_id
        app.organisation_id = invocation_snapshot.organisation_id or app.organisation_id
        app.app_key = invocation_snapshot.app_key or app.app_key or self.app_name
        app.app_id = str(
            invocation_snapshot.app_id
            or invocation_snapshot.app_install_id
            or app.app_id
            or app.app_key
        )
        event_payload: dict[str, Any] = {}

        status = "succeeded"
        error = None
        return_value = None
        log_records: list[logging.LogRecord] = []
        generated_files: list[Path] = []
        existing_output_files = (
            set(env.output_dir.rglob("*"))
            if env.output_dir is not None and env.output_dir.exists()
            else set()
        )
        handler = _ListHandler(log_records)
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            if env.output_dir is not None:
                env.output_dir.mkdir(parents=True, exist_ok=True)
            event_payload = self._refresh_event_snapshot(event)
            return_value = await app._handle_event(event_payload)
            if env.data_client.blocked_write_error is not None:
                status = "error"
                error = env.data_client.blocked_write_error
            else:
                processor_error = _processor_error_from_logs(log_records)
                if processor_error is not None:
                    status = "error"
                    error = processor_error
        except BaseException as exc:
            status = "error"
            error = exc
        finally:
            root.removeHandler(handler)
            if env.output_dir is not None and env.output_dir.exists():
                generated_files = [
                    path
                    for path in sorted(env.output_dir.rglob("*"))
                    if path.is_file() and path not in existing_output_files
                ]
            if close_env:
                env.__exit__(None, None, None)

        return ProcessorTestResult(
            status=status,
            return_value=return_value,
            error=error,
            logs=log_records,
            writes=env.data_client.recorded_writes,
            generated_files=generated_files,
            duration_ms=int((time.perf_counter() - started) * 1000),
            invocation=SimpleNamespace(
                app_name=self.app_name,
                app_key=invocation_snapshot.app_key or self.app_name,
                app_install=self.app_install,
                event_type=(event_payload.get("op") or "").removeprefix("on_"),
            ),
        )


class _ListHandler(logging.Handler):
    def __init__(self, records: list[logging.LogRecord]):
        super().__init__()
        self.records = records

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _processor_error_from_logs(records: list[logging.LogRecord]) -> RuntimeError | None:
    for record in records:
        if record.levelno < logging.ERROR:
            continue
        message = record.getMessage()
        if (
            "Error attempting to process event" in message
            or "Unhandled error in invocation" in message
        ):
            if record.exc_info and record.exc_info[1] is not None:
                exc = record.exc_info[1]
                return RuntimeError(f"{message}: {type(exc).__name__}: {exc}")
            return RuntimeError(message)
    return None
