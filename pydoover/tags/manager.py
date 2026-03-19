from __future__ import annotations

import time
from pydoover.models import Aggregate, EventSubscription

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from pydoover.utils.diff import apply_diff, generate_diff
from pydoover.utils.utils import call_maybe_async

if TYPE_CHECKING:
    from ..docker.device_agent.device_agent import DeviceAgentInterface

TAG_CLOUD_MAX_AGE = 60 * 60  # 1 hour
TAG_CHANNEL_NAME = "tag_values"
log = logging.getLogger("pydoover.tags.manager")


class KeyPath:
    """Represents a tag key as a normalized nested path."""

    def __init__(self, key: str | list[str] | KeyPath, app_key: str | None = None):
        if isinstance(key, KeyPath):
            self._path = key.path
            self.app_key = key.app_key
            self.key = key.key
            return

        if isinstance(key, str):
            path = [key]
        else:
            path = list(key)

        if not path or any(not isinstance(part, str) or not part for part in path):
            raise ValueError(
                "KeyPath requires one or more non-empty string path segments."
            )

        if app_key is not None:
            if not isinstance(app_key, str):
                raise ValueError("App key must be a string.")
            path.insert(0, app_key)

        self._path = path
        self.app_key = app_key
        self.key = key

    def get(self) -> list[str]:
        """Return the normalized path segments."""
        return list(self._path)

    @property
    def path(self) -> list[str]:
        return self._path

    def construct_dict(self, value):
        """Wrap a leaf value into a nested dict using this key path."""
        result = value
        for part in reversed(self.path):
            result = {part: result}
        return result

    def lookup_dict(self, d: dict[str, Any], raise_key_error: bool = False):
        """Resolve this key path against a nested dictionary."""
        current = d
        for part in self.path:
            if not isinstance(current, dict):
                return None
            try:
                current = current[part]
            except KeyError as e:
                if raise_key_error:
                    raise e
                return None
        return current

    def in_dict(self, d: dict[str, Any]):
        """Return ``True`` when this key path exists in a nested dictionary."""
        current = d
        for part in self.path:
            if not isinstance(current, dict):
                return False
            try:
                current = current[part]
            except KeyError:
                return False
        return True

    def __eq__(self, other: str | list[str] | KeyPath):
        """Define equality based on another key or KeyPath"""
        if isinstance(other, KeyPath):
            other = other.get()
        if not isinstance(other, list) and not isinstance(other, tuple):
            other = [other]
        for part in self.path:
            if part != other[0]:
                return False
            other.remove(part)
        return True

    def __hash__(self):
        """Define hash based on user_id"""
        return hash(".".join(self.path))


class TagsManager:
    """Base interface for manager-backed tag access."""

    def get_tag(
        self,
        key: str | list[str] | KeyPath,
        default: Any = None,
        app_key: str | None = None,
        raise_key_error: bool = False,
    ) -> Any | None:
        """Fetch a tag value from the backing store."""
        raise NotImplementedError

    async def set_tag(self, key: str, value: Any, app_key: str | None = None, flush: bool = False) -> None:
        """Set a tag value in the backing store."""
        raise NotImplementedError

    async def commit_tags(self) -> None:
        """Flush any buffered tag changes, if the implementation buffers them."""
        return


class TagsManagerDocker(TagsManager):
    """Tag manager for docker applications backed by the device agent channels."""

    def __init__(self, client: "DeviceAgentInterface" = None, tag_log_interval: int = TAG_CLOUD_MAX_AGE):
        self.client: DeviceAgentInterface = client
        self._is_async = True

        self._tag_values: dict[str, Any] = {}
        self._tag_subscriptions: dict[KeyPath, Callable] = {}
        
        self.tag_log_interval = tag_log_interval

        self._last_tag_log_time: float = 0.0
        self._pending_tag_log: dict[str, Any] = {}
        self._pending_tag_aggregate: dict[str, Any] = {}

        self._tags_dirty = False

    async def setup(self, skip_sync: bool = False):
        """Register the tag channel subscription with the backing client. Blocks until tags are synced."""
        self.client.add_event_callback(
            TAG_CHANNEL_NAME,
            self._wrap_aggregate_callback(self._on_tag_update),
            EventSubscription.aggregate_update,
        )

        if skip_sync:
            return

        await self.client.wait_for_channels_sync([TAG_CHANNEL_NAME], timeout=10)
        tag_agg: Aggregate = await self.client.fetch_channel_aggregate(TAG_CHANNEL_NAME)
        self._tag_values = tag_agg.data

    @staticmethod
    def _wrap_aggregate_callback(callback):
        async def _wrapper(event):
            data = event.aggregate.data if event.aggregate else {}
            await callback(data)

        return _wrapper

    async def _on_tag_update(self, tag_values: dict[str, Any]):
        diff = generate_diff(self._tag_values, tag_values, do_delete=False)
        self._tag_values = tag_values or {}
        await self.fulfill_tag_subscriptions(diff)

    async def fulfill_tag_subscriptions(self, diff):
        """Invoke any callbacks whose subscribed tag paths changed."""
        if diff is None or len(diff) == 0:
            return

        async def _wrap_callback(callback, tag_key, new_value):
            try:
                await asyncio.wait_for(
                    call_maybe_async(callback, tag_key, new_value), timeout=1
                )
            except Exception as e:
                log.exception(f"Error in {callback.__name__}: {e}", exc_info=e)

        for k, callback in self._tag_subscriptions.items():
            if k.in_dict(diff):
                await _wrap_callback(callback, k.key, k.lookup_dict(diff))

    def subscribe_to_tag(
        self,
        key: str | list[str] | KeyPath,
        callback: Callable[[str, dict[str, Any]], Awaitable[Any]]
        | Callable[[str, dict[str, Any]], Any],
        app_key: str = None,
    ):
        """Register a callback for updates to a tag path."""
        key_path = KeyPath(key, app_key=app_key)
        self._tag_subscriptions[key_path] = callback

    def unsubscribe_from_tag(
        self, key: str | list[str] | KeyPath, app_key: str | None = None
    ):
        """Remove a previously registered tag subscription."""
        key_path = KeyPath(key, app_key=app_key)
        if key_path in self._tag_subscriptions:
            del self._tag_subscriptions[key_path]

    def get_tag(
        self,
        key: str | list[str] | KeyPath,
        default: Any = None,
        app_key: str | None = None,
        raise_key_error: bool = False,
    ) -> Any | None:
        """Read a tag value from the locally cached tag channel state."""
        key_path = KeyPath(key, app_key=app_key)
        current_values = apply_diff(
            self._tag_values,
            self._pending_tag_aggregate,
            do_delete=False,
        )

        if not key_path.in_dict(current_values):
            log.debug(f"Tag {key_path} not found in current tags")
            if raise_key_error:
                raise KeyError(key_path)
            return default
        return key_path.lookup_dict(current_values)

    async def set_tag(
        self,
        key: str | list[str] | KeyPath,
        value: Any,
        app_key: str | None = None,
        only_if_changed: bool = True,
        flush: bool = False,
    ) -> None:
        """Set a single tag value and publish the resulting diff to the tag channel."""
        key_path = KeyPath(key, app_key=app_key)
        await self.set_tags(
            key_path.construct_dict(value), only_if_changed, flush=flush
        )

    async def set_tags(
        self,
        tags: dict[str, Any],
        only_if_changed: bool = True,
        key=None,
        app_key: str | None = None,
        flush: bool = False,
    ):
        """Publish multiple tag values to the device agent tag channel."""
        if key is not None or app_key is not None:
            tags = KeyPath(key, app_key=app_key).construct_dict(tags)

        if only_if_changed:
            diff = generate_diff(
                apply_diff(self._tag_values, self._pending_tag_aggregate, do_delete=False),
                tags,
                do_delete=False,
            )
            if len(diff) == 0:
                log.debug(
                    f"set_tags: tags={tags} Value did not change existing values {self._tag_values}"
                )
                return

        # Add to list of changes to be sent to the log
        apply_diff(self._pending_tag_log, tags, clone=False)

        if flush:
            log.debug(f"set_tags: tags={tags} Flushing to dda")
            apply_diff(self._pending_tag_aggregate, tags, clone=False)
            await self.client.update_channel_aggregate(
                TAG_CHANNEL_NAME,
                self._pending_tag_aggregate,
                max_age_secs=TAG_CLOUD_MAX_AGE,
            )
            apply_diff(self._tag_values, self._pending_tag_aggregate, clone=False)
            self._tags_dirty = False
            return

        # Just add to the pending aggregate to be flushed at the end of the main loop
        log.debug(f"set_tags: tags={tags} Added to pending aggregate")
        apply_diff(self._pending_tag_aggregate, tags, clone=False)
        self._tags_dirty = True

    async def commit_tags(self):
        """Publish a mesage with the changed tag values to the tag channel."""
        await self.flush_tags()
        
        now = time.time()
        if self._pending_tag_log and (
            now - self._last_tag_log_time >= self.tag_log_interval
        ):
            await self.flush_logs()

    async def flush_tags(self):
        """Flush any buffered tag changes."""
        
        if not self._tags_dirty:
            return False # Nothing to flush
        
        data = self._pending_tag_aggregate
        self._pending_tag_aggregate: dict[str, Any] = {}
        self._tags_dirty = False

        await self.client.update_channel_aggregate(TAG_CHANNEL_NAME, data, max_age_secs=TAG_CLOUD_MAX_AGE)
        apply_diff(self._tag_values, data, clone=False)

    async def flush_logs(self):
            
        if not self._pending_tag_log:
            return False # Nothing to flush
        
        log_data = self._pending_tag_log
        self._pending_tag_log = {}
        self._last_tag_log_time = time.time()

        await self.client.create_message(TAG_CHANNEL_NAME, log_data)

class TagsManagerProcessor(TagsManager):
    """Tag manager for cloud processor execution contexts."""

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
        self._is_async = True
        self._tag_values = tag_values or {}
        self._update_tags = False
        self._record_tag_update = record_tag_update

    def get_tag(
        self,
        key: str,
        default: Any = None,
        app_key: str | None = None,
        raise_key_error: bool = False,
    ) -> Any | None:
        """Read a tag value from the processor's in-memory tag payload."""
        app_key = app_key or self.app_key
        try:
            return self._tag_values[app_key][key]
        except (KeyError, TypeError) as exc:
            if raise_key_error:
                raise KeyError(key) from exc
            return default

    async def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
        """Update a tag value in the buffered processor payload."""
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

    async def commit_tags(self) -> None:
        """Flush any buffered tag changes back to the processor data API."""
        if not self._update_tags:
            return

        await self.client.update_aggregate(
            self.agent_id,
            TAG_CHANNEL_NAME,
            self._tag_values,
        )

        if self._record_tag_update:
            await self.client.publish_message(
                self.agent_id,
                TAG_CHANNEL_NAME,
                self._tag_values,
            )

        self._update_tags = False
