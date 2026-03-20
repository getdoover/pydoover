from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="run live integration tests against external Doover services",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: marks tests that call live external Doover services",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(reason="live tests skipped; pass --run-live to run them")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
