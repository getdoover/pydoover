from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path

import pytest

from pydoover.models.data import Aggregate, Channel, ChannelID, File, Message
from pydoover.processor import Application
from pydoover.reports import Application as ReportApplication
from pydoover.testing.processor import ProcessorSnapshot


FIXTURES = Path(__file__).parent / "fixtures_processor_testing"
MINIMAL_PROJECT = FIXTURES / "minimal_project"
SNAPSHOT_FILE = MINIMAL_PROJECT / "snapshots" / "minimal.snapshot.json"


def _processor_test_cls():
    try:
        from pydoover.testing.processor import ProcessorTest
    except ImportError as exc:
        raise AssertionError(
            "pydoover.testing.processor.ProcessorTest is the public v1 "
            "processor testing API"
        ) from exc

    return ProcessorTest


def _processor_test():
    return _processor_test_cls()("fixture_processor", app_install=456)


def _run(coro):
    return asyncio.run(coro)


class CapturingProcessor(Application):
    def __init__(self):
        super().__init__()
        self.seen = []

    def _common(self, event_type):
        return {
            "event_type": event_type,
            "agent_id": self.agent_id,
            "api_agent_id": self.api.agent_id,
            "organisation_id": self.api.organisation_id,
            "app_key": self.app_key,
            "app_id": self.app_id,
            "display_name": self.display_name,
        }

    async def on_message_create(self, event):
        self.seen.append(
            {
                **self._common("message_create"),
                "channel_agent_id": event.channel.agent_id,
                "message_author_id": event.message.author_id,
                "message_data": event.message.data,
            }
        )

    async def on_aggregate_update(self, event):
        self.seen.append(
            {
                **self._common("aggregate_update"),
                "channel_agent_id": event.channel.agent_id,
                "author_id": event.author_id,
                "event_organisation_id": event.organisation_id,
                "aggregate_data": event.aggregate.data,
                "request_data": event.request_data.data,
            }
        )

    async def on_deployment(self, event):
        self.seen.append(
            {
                **self._common("deployment"),
                "event_agent_id": event.agent_id,
                "event_app_id": event.app_id,
                "event_app_install_id": event.app_install_id,
                "event_app_key": event.app_key,
                "event_app_display_name": event.app_display_name,
            }
        )

    async def on_schedule(self, event):
        self.seen.append({**self._common("schedule"), "schedule_id": event.schedule_id})

    async def on_ingestion_endpoint(self, event):
        self.seen.append(
            {
                **self._common("ingestion"),
                "event_agent_id": event.agent_id,
                "event_organisation_id": event.organisation_id,
                "payload": event.payload,
            }
        )

    async def on_manual_invoke(self, event):
        self.seen.append(
            {
                **self._common("manual_invoke"),
                "event_organisation_id": event.organisation_id,
                "payload": event.payload,
            }
        )


def test_generated_files_use_single_processor_test_surface():
    test = _processor_test()

    assert hasattr(test, "Environment")
    assert hasattr(test, "events")
    assert hasattr(test, "processor")
    assert hasattr(test, "auth")
    assert hasattr(test, "run")

    env = test.Environment()
    env.data_client = test.processor.DataClient()
    env.auth = test.auth.cli_user_for_reads(profile="staging")

    assert hasattr(env, "__enter__")
    assert hasattr(env, "__exit__")
    assert hasattr(env.data_client, "reads")
    assert hasattr(env.data_client, "writes")


def test_event_builders_cover_all_processor_invocation_shapes():
    async def scenario():
        test = _processor_test()

        events = [
            await test.events.message_create(
                channel="telemetry",
                message_source="latest",
            ),
            await test.events.aggregate_update(
                channel="status",
                aggregate={"state": "idle"},
                request_data={"state": "running"},
                author_id=123,
                organisation_id=789,
            ),
            await test.events.deployment(
                agent_id=123,
                app_id=111,
                app_install_id=456,
                app_key="fixture_processor",
                app_display_name="Fixture Processor",
            ),
            await test.events.schedule(schedule_id=222),
            await test.events.ingestion(
                body={"device": "abc"},
                content_type="application/json",
                invocation_url="http://localhost/webhook",
            ),
            await test.events.manual_invoke(
                organisation_id=789,
                payload={"state": "running"},
            ),
        ]

        assert len(events) == 6
        for event in events:
            assert event is not None
            assert callable(getattr(event, "to_dict", None))
            assert isinstance(event.to_dict(), dict)

    _run(scenario())


def test_run_refreshes_generated_events_from_active_env_snapshot():
    async def scenario():
        processor = CapturingProcessor()
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=processor,
        )

        events = [
            await test.events.message_create(
                channel="telemetry",
                message_source="latest",
            ),
            await test.events.aggregate_update(
                channel="status",
                request_data={"state": "running"},
            ),
            await test.events.deployment(),
            await test.events.schedule(schedule_id=222),
            await test.events.ingestion(body={"device": "abc"}),
            await test.events.manual_invoke(payload={"state": "running"}),
        ]

        snapshot = ProcessorSnapshot(
            agent_id=321,
            organisation_id=987,
            app_key="active_fixture_processor",
            app_id=111,
            app_install_id=456,
            token="active-token",
            deployment_config={
                "APP_ID": 111,
                "APP_DISPLAY_NAME": "Active Fixture Processor",
                "dv_proc_config": {"inv_targets": []},
            },
            channels={
                "status": Channel(
                    "status",
                    321,
                    False,
                    None,
                    None,
                    Aggregate({"state": "idle"}, [], None),
                )
            },
            messages={
                "telemetry": [
                    Message(
                        9001,
                        321,
                        ChannelID(321, "telemetry"),
                        {"reading": 42},
                        [],
                    )
                ]
            },
        )

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(snapshot)
        env.data_client.writes.capture()

        with env:
            results = [await test.run(event) for event in events]

        assert [result.status for result in results] == ["succeeded"] * 6
        assert [item["event_type"] for item in processor.seen] == [
            "message_create",
            "aggregate_update",
            "deployment",
            "schedule",
            "ingestion",
            "manual_invoke",
        ]
        for item in processor.seen:
            assert item["agent_id"] == 321
            assert item["api_agent_id"] == 321
            assert item["organisation_id"] == 987
            assert item["app_key"] == "active_fixture_processor"
            assert item["app_id"] == 111
            assert item["display_name"] == "Active Fixture Processor"

        assert processor.seen[0]["channel_agent_id"] == 321
        assert processor.seen[0]["message_author_id"] == 321
        assert processor.seen[0]["message_data"] == {"reading": 42}
        assert processor.seen[1]["channel_agent_id"] == 321
        assert processor.seen[1]["author_id"] == 321
        assert processor.seen[1]["event_organisation_id"] == 987
        assert processor.seen[1]["aggregate_data"] == {"state": "idle"}
        assert processor.seen[1]["request_data"] == {"state": "running"}
        assert processor.seen[2]["event_agent_id"] == 321
        assert processor.seen[2]["event_app_id"] == 111
        assert processor.seen[2]["event_app_install_id"] == 456
        assert processor.seen[2]["event_app_key"] == "active_fixture_processor"
        assert processor.seen[2]["event_app_display_name"] == "Active Fixture Processor"
        assert processor.seen[3]["schedule_id"] == 222
        assert processor.seen[4]["event_agent_id"] == 321
        assert processor.seen[4]["event_organisation_id"] == 987
        assert processor.seen[4]["payload"] == {"device": "abc"}
        assert processor.seen[5]["event_organisation_id"] == 987
        assert processor.seen[5]["payload"] == {"state": "running"}

    _run(scenario())


def test_snapshot_helpers_are_async_and_return_mutable_snapshot_objects():
    async def scenario():
        test = _processor_test()
        data_client = test.processor.DataClient()

        assert inspect.iscoroutinefunction(data_client.reads.use_live_snapshot)
        assert inspect.iscoroutinefunction(data_client.reads.use_snapshot_file)

        snapshot = await data_client.reads.use_snapshot_file(SNAPSHOT_FILE)
        snapshot.processor_info.deployment_config["threshold"] = 42
        snapshot.processor_info.tag_values.setdefault("fixture_processor", {})[
            "enabled"
        ] = True
        snapshot.channels["status"].aggregate.data["state"] = "mutated"

        assert snapshot.processor_info.deployment_config["threshold"] == 42
        assert (
            snapshot.processor_info.tag_values["fixture_processor"]["enabled"] is True
        )
        assert snapshot.channels["status"].aggregate.data["state"] == "mutated"

    _run(scenario())


def test_nested_snapshot_schema_loads_processor_info_app_owner_and_timestamps():
    snapshot = ProcessorSnapshot.from_dict(
        {
            "app": {
                "local_name": "fixture_processor",
                "app_key": "fixture_processor",
                "app_id": 111,
                "app_install_id": 456,
            },
            "owner": {"agent_id": "123", "organisation_id": "789"},
            "processor_info": {
                "token": "snapshot-token",
                "deployment_config": {"APP_ID": 111, "APP_DISPLAY_NAME": "Fixture"},
                "tag_values": {"fixture_processor": {"enabled": True}},
                "ui_state": {"state": {}},
                "ui_cmds": {"fixture_processor": {"button": "pressed"}},
                "connection_data": {"config": {"offline_after": 60}},
            },
            "channels": {
                "status": {
                    "id": {"agent_id": "123", "name": "status"},
                    "aggregate": {
                        "data": {"state": "idle"},
                        "timestamp": 1780000000000,
                    },
                },
                "legacy": {
                    "name": "legacy",
                    "owner_id": "123",
                    "is_private": True,
                    "aggregate": {
                        "data": {"value": 7},
                        "last_updated": 1780000001000,
                    },
                },
            },
        }
    )

    assert snapshot.agent_id == 123
    assert snapshot.organisation_id == 789
    assert snapshot.app_key == "fixture_processor"
    assert snapshot.app_id == 111
    assert snapshot.app_install_id == 456
    assert snapshot.token == "snapshot-token"
    assert snapshot.processor_info.deployment_config["APP_DISPLAY_NAME"] == "Fixture"
    assert snapshot.processor_info.tag_values["fixture_processor"]["enabled"] is True
    assert snapshot.channels["status"].aggregate.data == {"state": "idle"}
    assert (
        int(snapshot.channels["status"].aggregate.last_updated.timestamp() * 1000)
        == 1780000000000
    )
    assert snapshot.channels["legacy"].is_private is True
    assert (
        int(snapshot.channels["legacy"].aggregate.last_updated.timestamp() * 1000)
        == 1780000001000
    )


def test_missing_fixture_reads_fail_when_delegation_is_disabled():
    async def scenario():
        test = _processor_test()
        data_client = test.processor.DataClient()

        data_client.reads.use_fixtures()
        data_client.reads.delegate_missing(False)

        with pytest.raises(Exception, match="missing_status"):
            await data_client.fetch_channel("missing_status", agent_id=123)

    _run(scenario())


def test_latest_message_source_fails_when_snapshot_data_is_missing():
    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=CapturingProcessor,
        )
        event = await test.events.message_create(
            channel="telemetry",
            message_source="latest",
        )

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="fixture_processor",
            )
        )
        env.data_client.reads.delegate_missing(False)

        with env:
            result = await test.run(event)

        assert result.status == "error"
        assert "Missing latest snapshot message" in str(result.error)

    _run(scenario())


def test_aggregate_update_fails_when_snapshot_channel_is_missing():
    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=CapturingProcessor,
        )
        event = await test.events.aggregate_update(channel="missing_status")

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="fixture_processor",
            )
        )
        env.data_client.reads.delegate_missing(False)

        with env:
            result = await test.run(event)

        assert result.status == "error"
        assert "Missing snapshot aggregate" in str(result.error)

    _run(scenario())


def test_live_snapshot_can_seed_requested_latest_message_placeholders():
    async def scenario():
        test = _processor_test()
        data_client = test.processor.DataClient()

        snapshot = await data_client.reads.use_live_snapshot(
            agent_id=123,
            app_key="fixture_processor",
            channels=["telemetry"],
            latest_messages=["telemetry"],
        )

        assert "telemetry" in snapshot.channels
        assert snapshot.messages["telemetry"][-1].channel.name == "telemetry"
        assert snapshot.messages["telemetry"][-1].data == {}

    _run(scenario())


def test_snapshot_backed_fetch_message_supports_report_manual_invokes():
    class SnapshotReport(ReportApplication):
        async def generate(self, agent_ids, period_start, period_end):
            return File("report.txt", "text/plain", 4, b"done")

    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=SnapshotReport,
        )
        event = await test.events.manual_invoke(payload={"report_id": 101})

        snapshot = ProcessorSnapshot(
            agent_id=123,
            organisation_id=789,
            app_key="fixture_processor",
            app_install_id=456,
            deployment_config={
                "APP_ID": 111,
                "APP_DISPLAY_NAME": "Fixture Report",
                "DEVICE_LIST": [321],
            },
            messages={
                "reports": [
                    Message(
                        101,
                        123,
                        ChannelID(123, "reports"),
                        {
                            "period_start": 1780000000000,
                            "period_end": 1780003600000,
                            "status": "Generating",
                            "logs": "",
                        },
                        [],
                    )
                ]
            },
        )

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(snapshot)
        env.data_client.reads.delegate_missing(False)
        env.data_client.writes.capture()

        with env:
            result = await test.run(event)

        assert result.status == "succeeded"
        assert result.writes[-1].method == "update_message"
        assert result.writes[-1].channel == "reports"
        assert result.writes[-1].files[0].filename == "report.txt"
        assert result.writes[-1].data["status"] == "Complete"

    _run(scenario())


def test_environment_output_dir_populates_generated_files(tmp_path):
    class FileWritingProcessor(Application):
        async def on_manual_invoke(self, event):
            Path(event.payload["output_dir"]).joinpath("result.txt").write_text(
                "generated"
            )

    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=FileWritingProcessor,
        )
        output_dir = tmp_path / "output"
        event = await test.events.manual_invoke(payload={"output_dir": str(output_dir)})

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="fixture_processor",
            )
        )
        env.files.output_dir(output_dir)

        with env:
            result = await test.run(event)

        assert result.status == "succeeded"
        assert result.generated_files == [output_dir / "result.txt"]
        assert result.to_summary()["generated_files"] == [
            str(output_dir / "result.txt")
        ]

    _run(scenario())


def test_captured_processor_writes_are_typed_and_serializable():
    async def scenario():
        test = _processor_test()
        data_client = test.processor.DataClient()

        data_client.writes.capture()
        await data_client.create_message(
            "status",
            {"state": "created"},
            agent_id=123,
            organisation_id=789,
        )
        await data_client.update_message(
            "status",
            101,
            {"state": "updated"},
            replace_data=True,
            agent_id=123,
            organisation_id=789,
        )
        await data_client.delete_message(
            "status",
            101,
            agent_id=123,
            organisation_id=789,
        )
        await data_client.create_channel(
            "alerts",
            is_private=True,
            message_schema={"type": "object"},
            agent_id=123,
            organisation_id=789,
        )
        await data_client.put_channel(
            "status",
            is_private=False,
            aggregate_schema={"type": "object"},
            agent_id=123,
            organisation_id=789,
        )
        await data_client.update_channel_aggregate(
            "status",
            {"state": "running"},
            agent_id=123,
            organisation_id=789,
            log_update=True,
            replace_keys=["state"],
        )

        assert [write.method for write in data_client.writes.recorded] == [
            "create_message",
            "update_message",
            "delete_message",
            "create_channel",
            "put_channel",
            "update_channel_aggregate",
        ]
        write = data_client.writes.recorded[-1]
        assert write.method == "update_channel_aggregate"
        assert write.agent_id == 123
        assert write.organisation_id == 789
        assert write.channel == "status"
        assert write.data == {"state": "running"}
        assert write.files == []
        assert write.options["log_update"] is True
        assert write.options["replace_keys"] == ["state"]
        assert isinstance(write.timestamp_ms, int)

        dicts = data_client.writes.to_dicts()
        json.dumps(dicts)
        assert dicts[-1] == {
            "method": "update_channel_aggregate",
            "agent_id": 123,
            "organisation_id": 789,
            "channel": "status",
            "data": {"state": "running"},
            "files": [],
            "options": {"log_update": True, "replace_keys": ["state"]},
            "timestamp_ms": write.timestamp_ms,
        }

    _run(scenario())


def test_sandbox_write_capture_keeps_invoking_channel_guard():
    async def scenario():
        test = _processor_test()
        data_client = test.processor.DataClient()
        data_client.agent_id = 123
        data_client.app_key = "fixture_processor"
        data_client._invoking_channel_name = "status"
        data_client.writes.capture()

        with pytest.raises(
            RuntimeError, match="Cannot publish to the invoking channel"
        ):
            await data_client.create_message("status", {"state": "loop"})

        with pytest.raises(
            RuntimeError, match="Cannot publish to the invoking channel"
        ):
            await data_client.update_channel_aggregate("status", {"state": "loop"})

        await data_client.create_message(
            "status",
            {"state": "allowed"},
            allow_invoking_channel=True,
        )
        assert data_client.writes.recorded[-1].channel == "status"

    _run(scenario())


def test_blocked_writes_make_processor_test_result_fail():
    class WritingProcessor(Application):
        async def on_manual_invoke(self, event):
            await self.api.create_message("status", {"state": event.payload["state"]})

    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=WritingProcessor,
        )
        event = await test.events.manual_invoke(payload={"state": "blocked"})

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="fixture_processor",
                app_install_id=456,
            )
        )
        env.data_client.writes.block()

        with env:
            result = await test.run(event)

        assert result.status == "error"
        assert isinstance(result.error, RuntimeError)
        assert "Processor write blocked: create_message" in str(result.error)

    _run(scenario())


def test_handler_exception_logs_make_processor_test_result_fail():
    class FailingProcessor(Application):
        async def on_manual_invoke(self, event):
            raise RuntimeError("boom")

    async def scenario():
        test = _processor_test_cls()(
            "fixture_processor",
            app_install=456,
            application=FailingProcessor,
        )
        event = await test.events.manual_invoke(payload={})

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="fixture_processor",
            )
        )

        with env:
            result = await test.run(event)

        assert result.status == "error"
        assert "Error attempting to process event" in str(result.error)
        assert "RuntimeError: boom" in str(result.error)

    _run(scenario())


def test_auth_helpers_are_explicit_about_read_only_cli_credentials():
    test = _processor_test()

    auth = test.auth.cli_user_for_reads(profile="staging")

    assert auth.profile == "staging"
    assert auth.purpose == "reads"
    assert auth.allow_writes is False
    assert "token" not in repr(auth).lower()


def test_explicit_environment_context_runs_processor_and_returns_rich_result(
    monkeypatch,
):
    async def scenario():
        monkeypatch.chdir(MINIMAL_PROJECT)
        test = _processor_test()

        event = await test.events.manual_invoke(
            organisation_id=789,
            payload={"state": "running"},
        )

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        await env.data_client.reads.use_snapshot_file(SNAPSHOT_FILE)
        env.data_client.reads.delegate_missing(False)
        env.data_client.writes.capture()
        env.auth = test.auth.cli_user_for_reads()

        with env:
            result = await test.run(event)

        assert result.status in {"success", "succeeded"}
        assert isinstance(result.duration_ms, int | float)
        assert result.duration_ms >= 0
        assert result.logs
        assert result.writes[0].method == "update_channel_aggregate"
        assert result.writes[0].channel == "status"
        assert result.writes[0].data == {"state": "running"}
        assert result.writes.to_dicts()[0]["method"] == "update_channel_aggregate"
        assert result.generated_files == []
        if isinstance(result.invocation, dict):
            assert result.invocation["app_key"] == "fixture_processor"
            assert result.invocation["event_type"] == "manual_invoke"
        else:
            assert result.invocation.app_key == "fixture_processor"
            assert result.invocation.event_type == "manual_invoke"

    _run(scenario())


def test_project_config_lambda_handler_resolves_src_layout_application(
    monkeypatch, tmp_path
):
    project = tmp_path / "lambda_project"
    package = project / "src" / "lambda_processor"
    package.mkdir(parents=True)
    (project / "doover_config.json").write_text(
        json.dumps(
            {
                "lambda_processor": {
                    "name": "lambda_processor",
                    "type": "PRO",
                    "lambda_config": {"Handler": "lambda_processor.handler"},
                }
            }
        )
    )
    (package / "__init__.py").write_text(
        """
from pydoover.processor import Application, run_app


class LambdaProcessorApplication(Application):
    async def on_manual_invoke(self, event):
        await self.api.update_channel_aggregate("status", event.payload)


def handler(event, context):
    return run_app(LambdaProcessorApplication(), event, context)
""".lstrip()
    )

    async def scenario():
        monkeypatch.chdir(project)
        test = _processor_test_cls()("lambda_processor", app_install=456)
        event = await test.events.manual_invoke(payload={"state": "running"})

        env = test.Environment()
        env.data_client = test.processor.DataClient()
        env.data_client.reads.use_fixtures(
            ProcessorSnapshot(
                agent_id=123,
                organisation_id=789,
                app_key="lambda_processor",
            )
        )
        env.data_client.writes.capture()

        with env:
            result = await test.run(event)

        assert result.status == "succeeded"
        assert result.writes[-1].method == "update_channel_aggregate"
        assert result.writes[-1].channel == "status"
        assert result.writes[-1].data == {"state": "running"}

    _run(scenario())
