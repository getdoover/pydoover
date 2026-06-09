from __future__ import annotations

import time
from datetime import datetime, timezone

from pydoover.models import EventSubscription, AggregateUpdateEvent, ChannelSyncEvent

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterable

from pydoover.utils.diff import apply_diff, generate_diff
from pydoover.utils.utils import call_maybe_async

if TYPE_CHECKING:
    from ..docker.device_agent.device_agent import DeviceAgentInterface

TAG_CLOUD_MAX_AGE = 60 * 15  # 15min
TAG_OBSERVED_MAX_AGE = 3  # 3 seconds
TAG_CHANNEL_NAME = "tag_values"
# Channel that `live=True` tags are streamed to as one-shot messages every
# main-loop iteration. Currently the same channel as the persisted tag
# values; point it at a dedicated channel if live traffic should be kept out
# of the tag-value message history.
LIVE_TAG_CHANNEL_NAME = "tag_values"
# Per-device "what is this user doing that touches this device" channel.
# Replaces the coarse `doover_ui_fastmode` aggregate with per-bucket presence:
#   {
#     "agent_open":    {<user_id>: <ts>},
#     "group_open":    {<user_id>: <ts>},
#     "app_open":      {<user_id>: {"ts": <ts>, "apps": [<app_key>, ...]}},
#     "live_tag_open": {<user_id>: {"ts": <ts>, "tags": [<tag_name>, ...]}},
#   }
# Timestamps are ms-since-epoch. The customer-site re-stamps every 120s while
# the tab is visible, so anything older than that is treated as gone.
UI_SUB_CHANNEL_NAME = "dv-ui-sub"
UI_SUB_FRESH_MS = 120_000

logger = logging.getLogger(__name__)


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


def _strip_paths(target: dict[str, Any], paths: dict[str, Any]) -> None:
    """Recursively remove leaf keys present in ``paths`` from ``target``.

    Used to dedupe the periodic-log buffer when the same keys have been
    promoted to the immediate-log buffer — avoids logging the same value
    twice (once now, once at the next 15-min flush).
    """
    for k, v in paths.items():
        if k not in target:
            continue
        if isinstance(v, dict) and isinstance(target[k], dict):
            _strip_paths(target[k], v)
            if not target[k]:
                del target[k]
        else:
            del target[k]


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

    async def set_tag(
        self,
        key: str,
        value: Any,
        app_key: str | None = None,
        flush: bool = False,
        log: bool = False,
    ) -> None:
        """Set a tag value in the backing store.

        ``log=True`` requests that this update be recorded as a logged
        data point as soon as possible (typically end of loop), rather
        than waiting for the next periodic log flush.
        """
        raise NotImplementedError

    async def commit_tags(self) -> None:
        """Flush any buffered tag changes, if the implementation buffers them."""
        return


class TagsManagerDocker(TagsManager):
    """Tag manager for docker applications backed by the device agent channels."""

    def __init__(
        self,
        client: "DeviceAgentInterface" = None,
        tag_log_interval: int = TAG_CLOUD_MAX_AGE,
        app_key: str | None = None,
    ):
        self.client: DeviceAgentInterface = client
        self.app_key = app_key

        self._tag_values: dict[str, Any] = {}
        self._tag_subscriptions: dict[KeyPath, Callable] = {}

        # Resolved (app_key, tag_name) paths for tags declared ``live=True``;
        # populated by ``set_live_tags`` once tag setup completes.
        self._live_tag_keys: list[KeyPath] = []

        self.tag_log_interval = tag_log_interval
        self.observed_max_age = TAG_OBSERVED_MAX_AGE
        self.default_max_age = TAG_CLOUD_MAX_AGE

        self._last_tag_log_time: float = 0.0
        self._pending_tag_log: dict[str, Any] = {}
        self._pending_immediate_log: dict[str, Any] = {}
        self._pending_tag_aggregate: dict[str, Any] = {}

        self._tags_dirty = False

        self.ui_sub_aggregate: dict[str, Any] = {}

    async def setup(self, skip_sync: bool = False):
        """Register the tag channel subscription with the backing client. Blocks until tags are synced."""
        self.client.add_event_callback(
            TAG_CHANNEL_NAME,
            self._on_tag_update,
            EventSubscription.aggregate_update,
        )
        self.client.add_event_callback(
            TAG_CHANNEL_NAME, self._on_tag_sync, EventSubscription.channel_sync
        )
        self.client.add_event_callback(
            UI_SUB_CHANNEL_NAME,
            self.on_ui_sub_update,
            EventSubscription.aggregate_update | EventSubscription.channel_sync,
        )

        if skip_sync:
            return

        await self.client.wait_for_channels_sync(
            [TAG_CHANNEL_NAME, UI_SUB_CHANNEL_NAME], timeout=10
        )

    async def on_ui_sub_update(self, event: AggregateUpdateEvent):
        self.ui_sub_aggregate = event.aggregate.data or {}

    def _fresh_bucket_entries(self, bucket: str) -> Iterable[Any]:
        """Yield the non-stale per-user entries from a ``dv-ui-sub`` bucket.

        Entries older than 120s are skipped — the customer-site re-stamps every
        120s while the tab is visible, so a stamp older than that means the
        claim has been dropped (or the tab was closed without a clean teardown).
        """
        entries = self.ui_sub_aggregate.get(bucket) or {}
        now_ms = datetime.now(tz=timezone.utc).timestamp() * 1000
        for entry in entries.values():
            if entry is None:
                continue
            ts = entry.get("ts") if isinstance(entry, dict) else entry
            if not isinstance(ts, (int, float)):
                continue
            if (now_ms - ts) < UI_SUB_FRESH_MS:
                yield entry

    @property
    def is_being_observed(self) -> bool:
        """Whether *any* user has an active claim on this agent.

        True if some user has the agent page open, has it rendered in a list
        context (group / map / sidebar), has any app expanded, or has live mode
        enabled on any tag. Coarse — for behaviour that should specifically
        track "is this app expanded" or "is this tag in live mode" use the
        narrower :attr:`is_app_open` / :attr:`is_live_tag_open` helpers.
        """
        return any(
            next(self._fresh_bucket_entries(bucket), None) is not None
            for bucket in ("agent_open", "group_open", "app_open", "live_tag_open")
        )

    @property
    def is_agent_open(self) -> bool:
        """Whether some user has this agent's page open."""
        return next(self._fresh_bucket_entries("agent_open"), None) is not None

    @property
    def is_group_open(self) -> bool:
        """Whether some user is viewing a context that renders this agent.

        Includes the group page, home, map, sidebar, header — anything where
        the customer-site renders the agent's icon. True even when the user is
        not on the agent's own page.
        """
        return next(self._fresh_bucket_entries("group_open"), None) is not None

    def is_live_tag_open(self, tag_name: str, app_key: str | None = None) -> bool:
        """Whether some user has this tag in live mode.

        ``tag_name`` matches the bare declared name; ``app_key`` defaults to
        this manager's own app. The customer-site qualifies tags as
        ``<app_key>.<tag_name>`` on the wire to disambiguate same-named tags
        across apps.
        """
        app_key = app_key if app_key is not None else self.app_key
        qualified = f"{app_key}.{tag_name}" if app_key else tag_name
        return qualified in self._live_tags_opened()

    @property
    def is_app_open(self) -> bool:
        """Whether some user has this app expanded on the customer-site.

        Drives ``max_age_secs`` — there's no point fast-publishing tag values
        when nobody has the application open.
        """
        if not self.app_key:
            return False
        return any(
            self.app_key in (entry.get("apps") or [])
            for entry in self._fresh_bucket_entries("app_open")
            if isinstance(entry, dict)
        )

    def _live_tags_opened(self) -> set[str]:
        """Tag names that some user has enabled live mode on for this agent."""
        opened: set[str] = set()
        for entry in self._fresh_bucket_entries("live_tag_open"):
            if isinstance(entry, dict):
                opened.update(entry.get("tags") or [])
        return opened

    @property
    def max_age_secs(self):
        return self.observed_max_age if self.is_app_open else self.default_max_age

    async def _on_tag_sync(self, event: ChannelSyncEvent):
        self._tag_values = event.aggregate.data

    async def _on_tag_update(self, event: AggregateUpdateEvent):
        diff = generate_diff(self._tag_values, event.aggregate.data, do_delete=False)
        self._tag_values = event.aggregate.data or {}
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
                logger.exception(f"Error in {callback.__name__}: {e}", exc_info=e)

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
            logger.debug(f"Tag {key_path} not found in current tags")
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
        log: bool = False,
    ) -> None:
        """Set a single tag value and publish the resulting diff to the tag channel."""
        key_path = KeyPath(key, app_key=app_key)
        await self.set_tags(
            key_path.construct_dict(value), only_if_changed, flush=flush, log=log
        )

    async def set_tags(
        self,
        tags: dict[str, Any],
        only_if_changed: bool = True,
        key=None,
        app_key: str | None = None,
        flush: bool = False,
        log: bool = False,
    ):
        """Publish multiple tag values to the device agent tag channel."""
        if key is not None or app_key is not None:
            tags = KeyPath(key, app_key=app_key).construct_dict(tags)

        if only_if_changed:
            diff = generate_diff(
                apply_diff(
                    self._tag_values, self._pending_tag_aggregate, do_delete=False
                ),
                tags,
                do_delete=False,
            )
            if len(diff) == 0:
                logger.debug(
                    f"set_tags: tags={tags} Value did not change existing values {self._tag_values}"
                )
                return

        if log:
            # Promote these paths to the immediate-log buffer (flushed at
            # end of loop) and drop any prior periodic-log entries for the
            # same paths so the same change isn't logged twice.
            apply_diff(self._pending_immediate_log, tags, do_delete=False, clone=False)
            _strip_paths(self._pending_tag_log, tags)
        else:
            # Add to list of changes to be sent to the logger. Preserve None so
            # ``tag.set(None)`` propagates upstream as "clear this tag" rather
            # than silently disappearing — the default ``do_delete=True`` would
            # pop the key from the pending diff before it ever leaves the client.
            apply_diff(self._pending_tag_log, tags, do_delete=False, clone=False)

        if flush:
            logger.debug(f"set_tags: tags={tags} Flushing to dda")
            apply_diff(self._pending_tag_aggregate, tags, do_delete=False, clone=False)
            await self.client.update_channel_aggregate(
                TAG_CHANNEL_NAME,
                self._pending_tag_aggregate,
                max_age_secs=self.max_age_secs,
            )
            apply_diff(self._tag_values, self._pending_tag_aggregate, clone=False)
            self._tags_dirty = False
            return

        # Just add to the pending aggregate to be flushed at the end of the main loop
        logger.debug(f"set_tags: tags={tags} Added to pending aggregate")
        apply_diff(self._pending_tag_aggregate, tags, do_delete=False, clone=False)
        self._tags_dirty = True

    async def commit_tags(self):
        """Publish a mesage with the changed tag values to the tag channel."""
        await self.flush_tags()
        await self.flush_live_tags()

        if self._pending_immediate_log:
            await self.flush_immediate_logs()

        now = time.time()
        if self._pending_tag_log and (
            now - self._last_tag_log_time >= self.tag_log_interval
        ):
            await self.flush_logs()

    async def flush_tags(self):
        """Flush any buffered tag changes."""

        if not self._tags_dirty:
            return False  # Nothing to flush

        data = self._pending_tag_aggregate
        self._pending_tag_aggregate: dict[str, Any] = {}
        self._tags_dirty = False

        await self.client.update_channel_aggregate(
            TAG_CHANNEL_NAME, data, max_age_secs=self.max_age_secs
        )
        apply_diff(self._tag_values, data, clone=False)

    def set_live_tags(self, keys: Iterable[KeyPath | tuple[str | None, str]]) -> None:
        """Register the tag paths that :meth:`flush_live_tags` should publish.

        Called by the application after tag setup with the resolved
        ``(app_key, tag_name)`` pairs of every ``live=True`` tag (see
        :meth:`pydoover.tags.Tags.get_live_tag_keys`).
        """
        self._live_tag_keys = [
            k if isinstance(k, KeyPath) else KeyPath(k[1], app_key=k[0]) for k in keys
        ]

    async def flush_live_tags(self):
        """Publish current values of ``live=True`` tags as a one-shot message.

        Called from :meth:`commit_tags` on every main-loop iteration, but only
        does anything for the subset of live tags that some user has enabled
        live mode on (``dv-ui-sub.live_tag_open.tags``) — there's no point
        streaming a live value when nothing is watching it. Sends a
        fire-and-forget snapshot so a watching UI gets fresh data without it
        being persisted as a logged message. No-op when no tags are declared
        ``live``, nobody has any of them in live mode, or no matching live tag
        currently has a value.
        """
        if not self._live_tag_keys:
            return False

        opened = self._live_tags_opened()
        if not opened:
            return False

        current = apply_diff(
            self._tag_values, self._pending_tag_aggregate, do_delete=False
        )
        payload: dict[str, Any] = {}
        for key_path in self._live_tag_keys:
            # The customer-site qualifies tags as "<app_key>.<tag_name>" to
            # avoid collisions across apps that happen to share a tag name.
            qualified = (
                f"{key_path.app_key}.{key_path.key}"
                if key_path.app_key
                else key_path.key
            )
            if qualified not in opened:
                continue
            if not key_path.in_dict(current):
                continue
            apply_diff(
                payload,
                key_path.construct_dict(key_path.lookup_dict(current)),
                do_delete=False,
                clone=False,
            )

        if not payload:
            return False

        await self.client.send_oneshot_message(LIVE_TAG_CHANNEL_NAME, payload)
        return True

    async def flush_logs(self, timestamp: datetime = None):
        if not self._pending_tag_log:
            return False  # Nothing to flush

        log_data = self._pending_tag_log
        self._pending_tag_log = {}
        self._last_tag_log_time = time.time()

        await self.client.create_message(
            TAG_CHANNEL_NAME, log_data, timestamp=timestamp
        )

    async def flush_immediate_logs(self, timestamp: datetime = None):
        """Flush any tag updates marked for immediate logging.

        Called from :meth:`commit_tags` at the end of every main loop
        iteration, so updates set with ``log=True`` become channel
        messages within a single loop rather than waiting up to 15
        minutes for the periodic log flush.
        """
        if not self._pending_immediate_log:
            return False  # Nothing to flush

        log_data = self._pending_immediate_log
        self._pending_immediate_log = {}

        await self.client.create_message(
            TAG_CHANNEL_NAME, log_data, timestamp=timestamp
        )
        return True

    async def log_history(
        self,
        points: Iterable[tuple[datetime, dict[str, Any]]],
        app_key: str | None = None,
    ) -> int:
        """Backfill historical logged tag values.

        Each ``(timestamp, tags)`` point is written as one logged message on the
        tag channel dated ``timestamp``, grouping all tags in that point into a
        single message. Unlike :meth:`set_tag` with ``log=True`` this does not
        touch current/live tag values or the pending-log buffers — it is purely
        for backdated points captured while the app wasn't running (e.g.
        sleep-log snapshots recorded while the compute module was off).

        One message is sent per point (there is no bulk message RPC); tags
        sharing a timestamp collapse into that single message. ``app_key``
        defaults to this manager's own app, matching where the app's own tags
        are stored (``{app_key: {tag_name: value}}``).

        Returns the number of messages written.
        """
        app_key = app_key if app_key is not None else self.app_key
        count = 0
        for timestamp, tags in points:
            if not tags:
                continue
            payload = {app_key: tags} if app_key else tags
            await self.client.create_message(
                TAG_CHANNEL_NAME, payload, timestamp=timestamp
            )
            count += 1
        return count


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
        self._tag_values = tag_values or {}
        self._update_tags = False
        self._record_tag_update = record_tag_update
        self._update_external_tags: bool = False

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

    async def set_tag(
        self,
        key: str,
        value: Any,
        app_key: str | None = None,
        flush: bool = False,
        log: bool = False,
    ) -> None:
        """Update a tag value in the buffered processor payload.

        ``log=True`` requests a logged data point in addition to the
        aggregate update — the message is created when
        :meth:`commit_tags` runs at the end of the processor invocation.
        """
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
        if log:
            self._record_tag_update = True
        if app_key != self.app_key:
            self._update_external_tags = True

    async def commit_tags(
        self, *, record_log: bool = False, timestamp: datetime | None = None
    ) -> None:
        """Flush any buffered tag changes back to the processor data API."""
        if not self._update_tags:
            return

        try:
            update = self._tag_values[self.app_key]
        except KeyError:
            update = None

        if self._update_external_tags:
            update = self._tag_values
        else:
            update = update and {self.app_key: update}

        # only publish if there are tags to publish.
        # Only publish external tags if requested explicitly (can cause recursion issues)
        if update:
            await self.client.update_channel_aggregate(TAG_CHANNEL_NAME, update)

            if self._record_tag_update or record_log:
                await self.client.create_message(
                    TAG_CHANNEL_NAME, update, timestamp=timestamp
                )

        self._update_tags = False
