Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the library.

Unreleased
----------
- Processors can now handle alarm state changes: override :meth:`pydoover.processor.Application.on_alarm_trigger` to receive an :class:`~pydoover.models.AlarmTriggerEvent` whenever an alarm on a subscribed channel changes state. The event carries the alarm, the states left and entered, the channel aggregate at trigger time, and the patch that caused it — plus ``is_alarm`` / ``is_cleared`` / ``value`` shortcuts. It fires for every transition, including ones whose user-facing notification the alarm silences
- :class:`pydoover.models.Alarm` now models the whole server-side alarm: ``topic_name``, ``notification_policy``, ``channel_name``, ``last_seen_ts``, ``alarm_pending_ms`` (debounce), the rate-of-change fields (``rate_threshold``, ``rate_window_ms`` and the read-only baseline pair) and per-state notification overrides via :class:`~pydoover.models.AlarmMessages` / :class:`~pydoover.models.AlarmStateMessage`. ``AlarmState.AlarmPending`` is now a known state — it previously raised on parse
- ``create_alarm`` / ``put_alarm`` accept the new alarm fields, and can create rate-of-change alarms (``rate_threshold`` in units per *second* plus ``rate_window_ms``, leaving ``value`` unset)
- ``update_alarm`` now distinguishes "leave alone" from "clear" for every nullable field, so a threshold alarm can be converted to a rate alarm and back. It also no longer drops ``expiry_mins`` when ``enabled`` is left unset
- Add ``list_agent_alarms`` for every alarm across an agent's channels
- Notification subscriptions support regex topic filters: ``topic_filter_mode`` on :class:`~pydoover.models.NotificationSubscription`, ``create_notification_subscription`` and ``update_notification_subscription``
- Add ``update_default_notification_subscription``, ``list_notification_endpoint_summaries`` (the sanitised listing available to a delegated subscription manager) and ``fetch_webpush_public_key``
- Add ``archive_channel`` / ``unarchive_channel``, and ``history_since`` / ``default_ttl`` on ``create_channel`` / ``put_channel``
- Add ``fetch_agent_permissions``, ``regenerate_schedule_token`` and ``invoke_ingestion_endpoint``
- Handlers can now see when a command they are still serving is cancelled by whoever issued it: :attr:`pydoover.rpc.RPCContext.cancelled`, :meth:`~pydoover.rpc.RPCContext.wait_cancelled` and :meth:`~pydoover.rpc.RPCContext.raise_if_cancelled`, plus :attr:`~pydoover.rpc.RPCContext.cancelled_by` / :attr:`~pydoover.rpc.RPCContext.cancelled_at` for the audit trail. Cancellation is cooperative — nothing interrupts the handler, so a handler that ignores it behaves exactly as before. Previously the update carrying the cancellation was received and silently discarded, leaving long sequences (a pump pre-start warning, a panel reboot) running with no way to stop them
- Add :func:`pydoover.rpc.status_is_cancelled` and :func:`pydoover.rpc.command_is_cancelled`. A cancelled command has no status code of its own — the site patches it to a terminal ``error`` carrying ``cancelled_at`` / ``cancelled_by`` — so these mirror the site's own reader rather than testing for a ``"cancelled"`` code that is never written
- Once a command has been cancelled, its handler no longer writes an outcome over the top. Reporting ``success`` would relabel a command the operator cancelled as having completed, losing the distinction between "cancelled in time" and "ran anyway"
- An outbound :meth:`pydoover.rpc.RPCManager.call` now raises :class:`pydoover.rpc.RPCCancelled` when the command is cancelled, rather than surfacing it as an opaque :class:`~pydoover.rpc.RPCError`
- A command that is already cancelled when it arrives is skipped rather than run, alongside the existing expiry check — a reconnect backlog can deliver the cancellation before the command itself
- Add ``log=True`` to :meth:`pydoover.tags.BoundTag.set` (and ``increment`` / ``decrement``) to publish a logged data point at the end of the current loop instead of waiting for the next periodic flush
- Add :meth:`pydoover.tags.BoundTag.delete` as the explicit alternative to ``tag.set(None)``
- Add typed tag classes :class:`pydoover.tags.Number`, :class:`pydoover.tags.Boolean`, and :class:`pydoover.tags.String` for tag declarations
- Add automatic logging triggers via a single ``log_on=`` kwarg taking descriptor objects: :class:`~pydoover.tags.Cross`, :class:`~pydoover.tags.Rise`, :class:`~pydoover.tags.Fall` (with optional ``deadband``) and :class:`~pydoover.tags.Delta` (absolute or percentage change from last logged value) for numerics; :class:`~pydoover.tags.AnyChange`, :class:`~pydoover.tags.Enter`, :class:`~pydoover.tags.Exit` for booleans and strings

v0.4.18
-------
- Add `MockDeviceAgentInterface` for testing purposes
- Fix issue with `wait_for_interval` not working correctly

v0.4.17
-------
- Fix issue with `listen_channel` not outputting to stderr correctly on connection error

v0.4.16
-------
- Fix issue with `listen_channel` not outputting to stdout correctly on connection error

v0.4.15
-------
- `RemoteComponent` now inherits from `Container` to support adding `children`.
- The default `serial_port` for `config.ModbusInterface` is now `/dev/ttyAMA0` to match the Doovit port.

v0.4.14
-------
- Wait up to 300 seconds for device agent to be ready before running `setup` in docker applications
- Add `log_formatter` and `log_filters` parameters to `run_app()`

v0.4.13
-------
- Fix bug with pydoover cli type hints
- Other minor fixes and features

v0.4.12
-------
- Fix issue with `log_threshold` in `ui.Variable`
- Fix issue with `set_tag` and `set_tags` in `cloud.Application`
- Fix issue with `set_tag` and `set_tags` in `cloud.Application`

v0.4.11
-------
- Add `disabled` to `ui.Action`
- Add built-in enum support for `config.Enum`
- Add default parameters to `get_tag` and `get_global_tag`
- Add support for `owner_org_key` in `cloud.Application`
- Add default device agent for device agent
- Fix issue with empty config schema
- Add default values for `ui.AlertStream`


v0.4.10
-------
- Add health checking for docker apps
- Add support for `additional_elements` in `config.ConfigSchema`
- Add generic `.attribute_name` support for `config.Object` objects.


v0.4.9
------
- Fix import error in `docker.platform_iface`

v0.4.8
------
- Add `get_immunity_seconds` and `set_immunity_seconds` to platform interface

v0.4.7
------
- Add message logging before a shutdown event is sent
- Add `create_alarm` to `doover.utils` package


v0.4.6
------
- New alarms util functionality
- New platform interface power management calls
- Improved main loop sleeping logic
- Bug fixes

v0.4.5
------
- Fix a problem with `get_di_events` and inconsistent return types between sync and async
- Set any missing config elements to their default value at runtime
- Add `ApplicationVariant` enum
- Don't process `shutdown_at` events before DDA is synced
- Add `__eq__` and `__repr__` methods to `Range` class
- Improve `is_being_observed` behaviour to disregard the device agent ID

v0.4.4
------
- Add a global_interaction parameter to ui.callback
- Fix interactions to work with app namespaces
- Change deprecated `.utcnow()` to `.now(tz=timezone.utc)`
- Separate staging and production config for applications in `doover_config.json`
- Fixes for publishing apps to the Doover App Store


v0.4.3
------
- Fix accidental extra argument in UI which stopped display names from setting

v0.4.2
------
- ConfigEntries are tz aware
- Make interaction docstring raw
- Only include deployment data if it exists
- Don't export some unnecessary _key values for app config

v0.4.1
------
- Remove explicit imports to allow usage without optional dependencies installed.

v0.4.0
------
- Support for new applications
- Support for offline DDA
- RTD documentation
- Open source pydoover
- Add testing structures
- Move to UV from Pipenv
- Add linting and automated testing

v0.3.0
-------
- TODO (various changes from unstable 5/3/2024)


v0.2.0
-------
- Add package to PyPi

v0.1.2
-------
- Add async support to modbus, camera and device agent docker services, while maintaining sync support.
- Autodetect saved doover config in API client (saved through CLI)
- Change interaction default behaviour to preserve current state
- Add colours to sliders in UI
- Add online/offline ticker status
- Add optional title to multiplot
- Add conditions argument to elements
- Add `get_channel_messages_in_window` API endpoint to fetch messages in a time window

v0.1.1
------
Initial version release of pydoover.

Primarily for testing CI/CD pipeline with Dockerhub deployments.

