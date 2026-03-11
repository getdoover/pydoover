from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from pydoover.utils.diff import apply_diff, generate_diff
from pydoover.utils.utils import call_maybe_async

from ..utils import get_is_async, maybe_async

TAG_CLOUD_MAX_AGE = 60 * 60  # 1 hour
TAG_CHANNEL_NAME = "tag_values"
log = logging.getLogger(__name__)


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
            raise ValueError("KeyPath requires one or more non-empty string path segments.")
          
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

    _is_async = False

    def get_tag(
        self,
        key: str | list[str] | KeyPath,
        default: Any = None,
        app_key: str | None = None,
        raise_key_error: bool = False,
    ) -> Any | None:
        """Fetch a tag value from the backing store."""
        raise NotImplementedError

    @maybe_async()
    def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
        """Set a tag value in the backing store."""
        raise NotImplementedError

    async def commit_tags(self) -> None:
        """Flush any buffered tag changes, if the implementation buffers them."""
        return


class TagsManagerDocker(TagsManager):
    """Tag manager for docker applications backed by the device agent channels."""

    def __init__(self, client = None, is_async = None):
        self.client = client
        self._is_async = get_is_async(is_async)
        
        self._tag_values = {}
        self._tag_subscriptions: dict[KeyPath, Callable] = {}
        self._tag_ready = asyncio.Event()

    def setup(self):
        """Register the tag channel subscription with the backing client."""
        self.client.add_subscription(TAG_CHANNEL_NAME, self._on_tag_update)
        
    async def await_tags_ready(self):
        """Wait until at least one tag update has been received."""
        if self._tag_ready.is_set():
            return
        await self._tag_ready.wait()

    async def _on_tag_update(self, _, tag_values: dict[str, Any]):
        diff = generate_diff(self._tag_values, tag_values, do_delete=False)
        self._tag_values = tag_values or {}
        await self.fulfill_tag_subscriptions(diff)

        # signifies the first tag update (or any subsequent tag update) has run and we are ready to start.
        self._tag_ready.set()
            
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
        
    def unsubscribe_from_tag(self, key: str | list[str] | KeyPath, app_key: str | None = None):
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
        if not key_path.in_dict(self._tag_values):
            log.debug(f"Tag {key_path} not found in current tags")
            if raise_key_error:
                raise KeyError(key_path)
            return default
        return key_path.lookup_dict(self._tag_values)

    @maybe_async()
    def set_tag(
        self,
        key: str | list[str] | KeyPath,
        value: Any,
        app_key: str | None = None,
        only_if_changed: bool = True,
    ) -> None:
        """Set a single tag value and publish the resulting diff to the tag channel."""
        key_path = KeyPath(key, app_key=app_key)
        self.set_tags(key_path.construct_dict(value), only_if_changed=only_if_changed)

    async def set_tag_async(
        self,
        key: str | list[str] | KeyPath,
        value: Any,
        app_key: str | None = None,
        only_if_changed: bool = True,
    ) -> None:
        """Async variant of :meth:`set_tag`."""
        key_path = KeyPath(key, app_key=app_key)
        await self.set_tags_async(key_path.construct_dict(value), only_if_changed)

    @maybe_async()
    def set_tags(
        self,
        tags: dict[str, Any],
        only_if_changed: bool = True,
        key = None,
        app_key: str | None = None,
    ):
        """Publish multiple tag values to the device agent tag channel."""
        if key is not None or app_key is not None:
            tags = KeyPath(key, app_key=app_key).construct_dict(tags)
            
        if only_if_changed:
            diff = generate_diff(self._tag_values, tags, do_delete=False)
            if len(diff) == 0:
                return

        apply_diff(self._tag_values, tags, clone=False)
        self.client.publish_to_channel(
            TAG_CHANNEL_NAME, tags, max_age=TAG_CLOUD_MAX_AGE, record_log=True
        )

    async def set_tags_async(
        self,
        tags: dict[str, Any],
        only_if_changed: bool = True,
        key = None,
        app_key: str | None = None,
    ):
        """Async variant of :meth:`set_tags`."""
        if key is not None or app_key is not None:
            tags = KeyPath(key, app_key=app_key).construct_dict(tags)
        
        if only_if_changed:
            diff = generate_diff(self._tag_values, tags, do_delete=False)
            if len(diff) == 0:
                return

        apply_diff(self._tag_values, tags, clone=False)
        await self.client.publish_to_channel_async(
            TAG_CHANNEL_NAME, tags, max_age=TAG_CLOUD_MAX_AGE, record_log=True
        )


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

    @maybe_async()
    def set_tag(self, key: str, value: Any, app_key: str | None = None) -> None:
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

    async def set_tag_async(
        self, key: str, value: Any, app_key: str | None = None
    ) -> None:
        """Async variant of :meth:`set_tag`."""
        self.set_tag(key, value, app_key=app_key, run_sync=True)

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
