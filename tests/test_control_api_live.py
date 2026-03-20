"""Live integration tests for pydoover.api.control.

These tests run against a live Doover Control API using a local auth profile.
By default they use the user's ``staging`` profile and the staging organisation
requested for these checks.

Run with:
    uv run pytest tests/test_control_api_live.py -v
"""

from __future__ import annotations

import os
import secrets
import sys
import time

import pytest

from pydoover.api import ControlClient
from pydoover.api.auth._config import ConfigManager
from pydoover.models.control import Device, DeviceType, Group


CONTROL_PROFILE = os.environ.get("PYDOOVER_CONTROL_PROFILE", "staging")
CONTROL_ORGANISATION_ID = 160537971806708483
GROUP_A1_NAME = "Group A.1 (DO NOT TOUCH)"
GROUP_B_NAME = "Group B (DO NOT TOUCH)"
GROUP_C_NAME = "Group C (DO NOT TOUCH)"
DEVICE_TYPE_NAME = "Doovit"
RENAMED_ICON = "microchip"

skip_no_profile = pytest.mark.skipif(
    ConfigManager().get(CONTROL_PROFILE) is None,
    reason=f"Doover auth profile {CONTROL_PROFILE!r} is required",
)


def _make_name(resource_type: str) -> str:
    return f"Test_{resource_type}_{secrets.token_hex(4)}"


def _find_group_by_name(client: ControlClient, name: str) -> Group:
    page = client.groups.list(search=name, per_page=100)
    for group in page.results:
        if group.name == name:
            return group
    raise AssertionError(f"Expected group {name!r} to exist in organisation {CONTROL_ORGANISATION_ID}.")


def _find_device_type_by_name(client: ControlClient, name: str) -> DeviceType:
    page = client.devices.types_list(search=name, per_page=50)
    for device_type in page.results:
        if device_type.name == name:
            return device_type
    raise AssertionError(f"Expected device type {name!r} to exist in organisation {CONTROL_ORGANISATION_ID}.")


def _find_group_in_tree(groups: list[dict], name: str) -> dict | None:
    for group in groups:
        if group.get("name") == name:
            return group
        found = _find_group_in_tree(group.get("children", []), name)
        if found is not None:
            return found
    return None


def _wait_for_agents_payload(client: ControlClient, group_name: str, timeout: float = 15.0) -> dict:
    deadline = time.monotonic() + timeout
    last_payload: dict | None = None
    while time.monotonic() < deadline:
        # The generated /agents/ endpoint currently exposes no response schema,
        # so use the control executor directly to validate the live payload.
        payload = client._execute("GET", "/agents/", response_kind="raw")
        last_payload = payload
        group = _find_group_in_tree(payload.get("groups", []), group_name)
        if group is not None:
            return payload
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for /agents/ to include group {group_name!r}. Last payload keys: "
        f"{sorted((last_payload or {}).keys())}"
    )


def _wait_for_group_under_parent(
    client: ControlClient,
    *,
    parent_name: str,
    child_name: str,
    timeout: float = 15.0,
) -> tuple[dict, dict]:
    deadline = time.monotonic() + timeout
    last_payload: dict | None = None
    while time.monotonic() < deadline:
        payload = client._execute("GET", "/agents/", response_kind="raw")
        last_payload = payload
        parent = _find_group_in_tree(payload.get("groups", []), parent_name)
        if parent is not None:
            child = _find_group_in_tree(parent.get("children", []), child_name)
            if child is not None:
                return payload, child
        time.sleep(1.0)
    raise AssertionError(
        f"Timed out waiting for group {child_name!r} under parent {parent_name!r}. Last payload keys: "
        f"{sorted((last_payload or {}).keys())}"
    )


@skip_no_profile
def test_control_live_staging_group_device_lifecycle():
    group_name = _make_name("Group")
    device_y_name = _make_name("Device")
    device_z_name = _make_name("Device")
    renamed_group_name = f"{group_name}_renamed"
    renamed_device_y_name = f"{device_y_name}_renamed"

    created_group_id: str | None = None
    created_device_y_id: str | None = None
    created_device_z_id: str | None = None

    with ControlClient(
        profile=CONTROL_PROFILE,
        organisation_id=CONTROL_ORGANISATION_ID,
        timeout=30.0,
    ) as client:
        parent_group_a1 = _find_group_by_name(client, GROUP_A1_NAME)
        parent_group_b = _find_group_by_name(client, GROUP_B_NAME)
        parent_group_c = _find_group_by_name(client, GROUP_C_NAME)
        doovit_type = _find_device_type_by_name(client, DEVICE_TYPE_NAME)

        try:
            group_x = client.groups.create(
                {
                    "name": group_name,
                    "parent_id": str(parent_group_a1.id),
                }
            )
            assert isinstance(group_x, Group)
            assert group_x.name == group_name
            created_group_id = str(group_x.id)

            device_y = client.devices.create(
                {
                    "name": device_y_name,
                    "display_name": device_y_name,
                    "group_id": created_group_id,
                    "type_id": str(doovit_type.id),
                }
            )
            assert isinstance(device_y, Device)
            assert device_y.display_name == device_y_name
            assert str(device_y.group.id) == created_group_id
            assert device_y.type.name == DEVICE_TYPE_NAME
            created_device_y_id = str(device_y.id)

            device_z = client.devices.create(Device(name=device_z_name, display_name=device_z_name, group=group_x, type=doovit_type.id))
            assert isinstance(device_z, Device)
            assert device_z.display_name == device_z_name
            assert str(device_z.group.id) == created_group_id
            assert device_z.type.name == DEVICE_TYPE_NAME
            assert device_z.name == device_z_name
            created_device_z_id = str(device_z.id)

            agents_payload, group_x_node = _wait_for_group_under_parent(
                client,
                parent_name=GROUP_A1_NAME,
                child_name=group_name,
            )
            assert {"agents", "groups", "organisation_users", "superusers"} <= set(agents_payload)
            assert group_x_node["id"] == created_group_id
            assert group_x_node["archived"] is False

            group_x = client.groups.partial(created_group_id, {"name": renamed_group_name})
            assert group_x.name == renamed_group_name

            device_y = client.devices.partial(
                created_device_y_id,
                {
                    "name": renamed_device_y_name,
                    "display_name": renamed_device_y_name,
                    "fa_icon": RENAMED_ICON,
                },
            )
            assert device_y.display_name == renamed_device_y_name
            assert device_y.fa_icon == RENAMED_ICON

            client.groups.partial(created_group_id, {"parent_id": str(parent_group_c.id)})
            _, group_x_node = _wait_for_group_under_parent(
                client,
                parent_name=GROUP_C_NAME,
                child_name=renamed_group_name,
            )
            assert group_x_node["id"] == created_group_id

            device_z = client.devices.partial(
                created_device_z_id,
                {"group_id": str(parent_group_b.id)},
            )
            assert str(device_z.group.id) == str(parent_group_b.id)
            assert device_z.group.name == GROUP_B_NAME

            device_y = client.devices.archive(created_device_y_id)
            assert device_y.archived is True

            device_z = client.devices.archive(created_device_z_id)
            assert device_z.archived is True

            group_x = client.groups.archive(created_group_id)
            assert group_x.archived is True
        finally:
            cleanup_errors: list[str] = []

            for device_id in (created_device_y_id, created_device_z_id):
                if device_id is None:
                    continue
                try:
                    device = client.devices.retrieve(device_id)
                    if not device.archived:
                        client.devices.archive(device_id)
                except Exception as exc:  # pragma: no cover - best-effort live cleanup
                    cleanup_errors.append(f"device {device_id}: {type(exc).__name__}: {exc}")

            if created_group_id is not None:
                try:
                    group = client.groups.retrieve(created_group_id)
                    if not group.archived:
                        client.groups.archive(created_group_id)
                except Exception as exc:  # pragma: no cover - best-effort live cleanup
                    cleanup_errors.append(f"group {created_group_id}: {type(exc).__name__}: {exc}")

            if cleanup_errors and sys.exc_info()[0] is None:
                pytest.fail("Control API live test cleanup failed: " + "; ".join(cleanup_errors))
