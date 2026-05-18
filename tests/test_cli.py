import argparse
from datetime import datetime, timezone
import json

from pydoover.cli.cli import CLI
from pydoover.cli.decorators import command
from pydoover.cli.sub_section import SubSection


class FakeInterface:
    def __init__(self, app_key: str, uri: str = "localhost:50051"):
        self.app_key = app_key
        self.uri = uri

    @command()
    def get_payload(self):
        return {"ok": True, "items": [1, 2]}

    @command()
    def get_nested_payload(self):
        return [
            FakeModel(1),
            {
                "inner": FakeModel(2),
                "when": datetime(2026, 5, 19, 1, 2, 3, tzinfo=timezone.utc),
            },
        ]

    @command()
    def send_at(self, timestamp: datetime | None = None):
        return {"timestamp": timestamp}


class FakeModel:
    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {"value": self.value}


def _run_fake_cli(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand")
    SubSection(FakeInterface, name="fake").mount_sub_section(subparsers)

    parsed = parser.parse_args(args)
    parsed.callback(**vars(parsed))


def test_cli_json_flag_outputs_valid_json(capsys):
    _run_fake_cli(["fake", "get_payload", "--json"])

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"ok": True, "items": [1, 2]}


def test_cli_default_output_remains_python_repr(capsys):
    _run_fake_cli(["fake", "get_payload"])

    captured = capsys.readouterr()
    assert captured.out == "{'ok': True, 'items': [1, 2]}\n"


def test_cli_json_flag_serializes_nested_models_and_datetimes(capsys):
    _run_fake_cli(["fake", "get_nested_payload", "--json"])

    captured = capsys.readouterr()
    assert json.loads(captured.out) == [
        {"value": 1},
        {"inner": {"value": 2}, "when": "2026-05-19T01:02:03+00:00"},
    ]


def test_cli_accepts_optional_datetime_arguments(capsys):
    _run_fake_cli(
        ["fake", "send_at", "--timestamp", "2026-05-19T01:02:03+00:00", "--json"]
    )

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"timestamp": "2026-05-19T01:02:03+00:00"}


def test_cli_exception_handler_does_not_require_debug_attr(monkeypatch, capsys):
    def fail():
        raise RuntimeError("boom")

    monkeypatch.setattr("sys.argv", ["pydoover"])
    monkeypatch.setattr(
        "argparse.ArgumentParser.parse_args",
        lambda self: argparse.Namespace(callback=fail),
    )

    CLI()

    captured = capsys.readouterr()
    assert captured.out.endswith("An error occurred: boom\n")
