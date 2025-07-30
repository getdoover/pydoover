Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the library.

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

