Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the library.

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

