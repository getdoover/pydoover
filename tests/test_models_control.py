import importlib.util
import inspect

import pydoover.models.control as control
from pydoover.models.control import (
    Application,
    CONTROL_SCHEMA_REGISTRY,
    ControlPage,
    Device,
    DeviceType,
    Group,
    Location,
    Organisation,
    Theme,
)


THEME_WITH_ID = {
    "id": 1,
    "accent_colour": "#112233",
    "brand_logo_colour": "#445566",
    "navbar_colour": "#778899",
    "navbar_text_colour": "#ffffff",
    "sidebar_colour": "#101010",
    "sidebar_text_colour": "#eeeeee",
    "banner_image": None,
}


def test_control_models_are_canonical_only():
    assert importlib.util.find_spec("pydoover.models.control.transport") is None
    assert not hasattr(control, "ThemeWithId")
    assert not hasattr(control, "ThemeWithIdRequest")
    assert not hasattr(control, "PaginatedThemeWithIdList")


def test_location_round_trips():
    location = Location.from_dict({"latitude": -33.86, "longitude": 151.21})

    assert location.to_dict() == {"latitude": -33.86, "longitude": 151.21}


def test_organisation_from_version_uses_schema_version_metadata():
    organisation = Organisation.from_version(
        "BasicOrganisationDetail",
        {"id": 101, "name": "Example Org", "archived": False},
    )

    assert organisation.id == 101
    assert organisation.name == "Example Org"
    assert organisation.archived is False
    assert organisation.to_version("BasicOrganisationDetail") == {
        "id": 101,
        "name": "Example Org",
        "archived": False,
    }


def test_device_request_serialization_uses_output_id_mapping():
    device = Device(
        name="device-1",
        display_name="Device One",
        type=DeviceType(id=201),
        group=Group(id=301),
        fixed_location=Location(latitude=-33.86, longitude=151.21),
        solution_config={"mode": "auto"},
    )

    payload = device.to_version("DeviceSerializerDetailRequest", method="POST")

    assert payload["display_name"] == "Device One"
    assert payload["type_id"] == 201
    assert payload["group_id"] == 301
    assert payload["fixed_location"] == {
        "latitude": -33.86,
        "longitude": 151.21,
    }
    assert payload["solution_config"] == {"mode": "auto"}


def test_device_resource_fields_accept_bare_ids():
    device = Device(
        name="device-2",
        display_name="Device Two",
        type=201,
        group=301,
    )

    assert isinstance(device.type, DeviceType)
    assert device.type.id == 201
    assert isinstance(device.group, Group)
    assert device.group.id == 301
    assert device.to_version("DeviceSerializerDetailRequest", method="POST") == {
        "name": "device-2",
        "display_name": "Device Two",
        "type_id": 201,
        "group_id": 301,
    }


def test_application_request_serializes_required_nullable_resource_fields_as_null():
    application = Application(
        name="processor-app",
        display_name="Processor App",
        description="Processor app",
        type="processor",
        visibility="private",
        depends_on=[],
        organisation=None,
        container_registry_profile=None,
    )

    assert application.to_version("ApplicationSerializerDetailRequest", method="POST") == {
        "name": "processor-app",
        "display_name": "Processor App",
        "description": "Processor app",
        "type": "processor",
        "visibility": "private",
        "depends_on": [],
        "organisation_id": None,
        "container_registry_profile_id": None,
    }


def test_required_non_nullable_fields_still_raise_when_missing_from_version_payload():
    device = Device(display_name="Device Only")

    try:
        device.to_version("DeviceSerializerDetailRequest", method="POST")
    except TypeError as exc:
        assert "Missing required field" in str(exc)
        assert "DeviceSerializerDetailRequest" in str(exc)
    else:
        raise AssertionError("Expected TypeError for missing required non-nullable field")


def test_control_models_expose_field_annotations_for_type_checkers():
    assert Device.__annotations__["display_name"] == "str"
    assert Device.__annotations__["group"] == "Group"
    assert Device.__annotations__["fa_icon"] == "str | None"


def test_control_models_expose_typed_constructor_signatures():
    signature = inspect.signature(Device)

    assert "display_name" in signature.parameters
    assert "group" in signature.parameters
    assert str(signature.parameters["display_name"].annotation) == "str | None"
    assert (
        str(signature.parameters["group"].annotation)
        == "Group | dict[str, Any] | str | int | None"
    )


def test_control_page_round_trips_with_canonical_models():
    page = ControlPage.from_dict(
        {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [THEME_WITH_ID],
        },
        Theme,
    )

    assert page.count == 1
    assert isinstance(page.results[0], Theme)
    assert page.to_dict()["results"][0]["id"] == 1


def test_control_schema_registry_preserves_exact_schema_names():
    assert CONTROL_SCHEMA_REGISTRY["ThemeSerializerWithIdList"] == {
        "kind": "model",
        "model": "Theme",
        "version": "ThemeSerializerWithIdList",
    }
    assert CONTROL_SCHEMA_REGISTRY["PaginatedThemeSerializerWithIdListList"] == {
        "kind": "page",
        "model": "Theme",
        "version": "ThemeSerializerWithIdList",
    }
