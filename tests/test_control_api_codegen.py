from pydoover.api.control._generated_async import OPERATION_COUNT as ASYNC_OPERATION_COUNT
from pydoover.api.control._generated_groups import (
    EXCLUDED_PATHS,
    GROUP_TREE,
    INCLUDED_OPERATION_IDS,
    OPERATION_COUNT,
)
from pydoover.api.control._generated_sync import OPERATION_COUNT as SYNC_OPERATION_COUNT


def test_generated_group_tree_matches_expected_surface():
    assert OPERATION_COUNT == 299
    assert SYNC_OPERATION_COUNT == 299
    assert ASYNC_OPERATION_COUNT == 299
    assert "public" not in GROUP_TREE
    assert "pwa" not in GROUP_TREE
    assert GROUP_TREE["container"] == {"registry": {}}
    assert "billing" in GROUP_TREE["organisations"]
    assert "products" in GROUP_TREE["organisations"]["billing"]
    assert "pending_users" in GROUP_TREE["organisations"]


def test_codegen_keeps_requested_paths_excluded():
    assert EXCLUDED_PATHS == [
        "/manifest.webmanifest",
        "/public/applications/",
        "/pwa_icon/{size}/",
        "/pwa_install_screenshot/",
        "/pwa_splash/{width}/{height}/{scale}/{orientation}/",
    ]


def test_included_operation_ids_cover_expected_examples():
    assert "applications_list" in INCLUDED_OPERATION_IDS
    assert "devices_installer_tarball_retrieve" in INCLUDED_OPERATION_IDS
    assert "organisations_billing_products_list" in INCLUDED_OPERATION_IDS
    assert "organisations_pending_users_approve_create" in INCLUDED_OPERATION_IDS
