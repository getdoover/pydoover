from datetime import datetime, timezone

import pytest

from pydoover.utils.snowflake import generate_snowflake_id_at
from pydoover.models import (
    Aggregate,
    AggregateUpdateEvent,
    Attachment,
    Channel,
    ChannelID,
    ConnectionConfig,
    ConnectionStatus,
    ConnectionType,
    DeploymentEvent,
    DooverConnectionStatus,
    EventSubscription,
    File,
    IngestionEndpointEvent,
    ManualInvokeEvent,
    Message,
    MessageCreateEvent,
    MessageUpdateEvent,
    OneShotMessage,
    ScheduleEvent,
    TurnCredential,
)


# ── fixtures ──────────────────────────────────────────────────────────


CHANNEL_ID_DICT = {"agent_id": "12345", "name": "test_channel"}

ATTACHMENT_DICT = {
    "filename": "photo.jpg",
    "content_type": "image/jpeg",
    "size": 1024,
    "url": "https://example.com/photo.jpg",
}

MESSAGE_DICT = {
    "id": "99999",
    "author_id": "11111",
    "channel": CHANNEL_ID_DICT,
    "data": {"temperature": 22.5},
    "attachments": [ATTACHMENT_DICT],
}

AGGREGATE_DICT = {
    "data": {"status": "ok", "count": 42},
    "attachments": [ATTACHMENT_DICT],
    "last_updated": 1700000000000,
}

CHANNEL_DICT = {
    "name": "sensor_data",
    "owner_id": "55555",
    "is_private": False,
    "aggregate_schema": {"type": "object"},
    "message_schema": None,
    "aggregate": AGGREGATE_DICT,
}


# ── ChannelID ─────────────────────────────────────────────────────────


class TestChannelID:
    def test_from_dict(self):
        ch = ChannelID.from_dict(CHANNEL_ID_DICT)
        assert ch.agent_id == 12345
        assert ch.name == "test_channel"

    def test_to_dict(self):
        ch = ChannelID(12345, "test_channel")
        assert ch.to_dict() == {"agent_id": 12345, "name": "test_channel"}

    def test_roundtrip_dict(self):
        ch = ChannelID.from_dict(CHANNEL_ID_DICT)
        d = ch.to_dict()
        ch2 = ChannelID.from_dict(d)
        assert ch2.agent_id == ch.agent_id
        assert ch2.name == ch.name

    def test_roundtrip_proto(self):
        ch = ChannelID(12345, "test_channel")
        proto = ch.to_proto()
        ch2 = ChannelID.from_proto(proto)
        assert ch2.agent_id == ch.agent_id
        assert ch2.name == ch.name


# ── Attachment ────────────────────────────────────────────────────────


class TestAttachment:
    def test_from_dict(self):
        a = Attachment.from_dict(ATTACHMENT_DICT)
        assert a.filename == "photo.jpg"
        assert a.content_type == "image/jpeg"
        assert a.size == 1024
        assert a.url == "https://example.com/photo.jpg"

    def test_to_dict(self):
        a = Attachment("photo.jpg", "image/jpeg", 1024, "https://example.com/photo.jpg")
        assert a.to_dict() == ATTACHMENT_DICT

    def test_roundtrip_dict(self):
        a = Attachment.from_dict(ATTACHMENT_DICT)
        a2 = Attachment.from_dict(a.to_dict())
        assert a2.filename == a.filename
        assert a2.size == a.size

    def test_roundtrip_proto(self):
        a = Attachment("test.txt", "text/plain", 512, "https://example.com/test.txt")
        proto = a.to_proto()
        a2 = Attachment.from_proto(proto)
        assert a2.filename == a.filename
        assert a2.content_type == a.content_type
        assert a2.size == a.size
        assert a2.url == a.url

    def test_optional_content_type(self):
        d = {**ATTACHMENT_DICT}
        del d["content_type"]
        a = Attachment.from_dict(d)
        assert a.content_type is None


# ── File ──────────────────────────────────────────────────────────────


class TestFile:
    def test_roundtrip_proto(self):
        f = File("data.bin", "application/octet-stream", 256, b"\x00\x01\x02")
        proto = f.to_proto()
        f2 = File.from_proto(proto)
        assert f2.filename == f.filename
        assert f2.content_type == f.content_type
        assert f2.size == f.size
        assert f2.data == f.data


# ── Message ───────────────────────────────────────────────────────────


class TestMessage:
    def test_from_dict(self):
        m = Message.from_dict(MESSAGE_DICT)
        assert m.id == 99999
        assert m.author_id == 11111
        assert m.channel.name == "test_channel"
        assert m.data == {"temperature": 22.5}
        assert len(m.attachments) == 1
        assert m.attachments[0].filename == "photo.jpg"

    def test_to_dict(self):
        m = Message.from_dict(MESSAGE_DICT)
        d = m.to_dict()
        assert d["id"] == 99999
        assert d["data"] == {"temperature": 22.5}
        assert len(d["attachments"]) == 1

    def test_roundtrip_dict(self):
        m = Message.from_dict(MESSAGE_DICT)
        m2 = Message.from_dict(m.to_dict())
        assert m2.id == m.id
        assert m2.data == m.data
        assert m2.channel.name == m.channel.name

    def test_roundtrip_proto(self):
        m = Message(
            id=99999,
            author_id=11111,
            channel=ChannelID(12345, "test_channel"),
            data={"temperature": 22.5},
            attachments=[],
        )
        proto = m.to_proto()
        m2 = Message.from_proto(proto)
        assert m2.id == m.id
        assert m2.author_id == m.author_id
        assert m2.channel.name == m.channel.name
        assert m2.data == m.data

    def test_empty_attachments(self):
        d = {**MESSAGE_DICT}
        del d["attachments"]
        m = Message.from_dict(d)
        assert m.attachments == []


# ── Aggregate ─────────────────────────────────────────────────────────


class TestAggregate:
    def test_from_dict(self):
        a = Aggregate.from_dict(AGGREGATE_DICT)
        assert a.data == {"status": "ok", "count": 42}
        assert len(a.attachments) == 1
        assert a.last_updated is not None

    def test_to_dict(self):
        a = Aggregate.from_dict(AGGREGATE_DICT)
        d = a.to_dict()
        assert d["data"] == {"status": "ok", "count": 42}
        assert len(d["attachments"]) == 1
        assert d["last_updated"] is not None

    def test_roundtrip_dict(self):
        a = Aggregate.from_dict(AGGREGATE_DICT)
        a2 = Aggregate.from_dict(a.to_dict())
        assert a2.data == a.data
        assert len(a2.attachments) == len(a.attachments)

    def test_roundtrip_proto(self):
        a = Aggregate(
            data={"key": "value"},
            attachments=[],
            last_updated=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        proto = a.to_proto()
        a2 = Aggregate.from_proto(proto)
        assert a2.data == a.data
        assert a2.attachments == []
        assert a2.last_updated is not None

    def test_none_last_updated(self):
        d = {"data": {"x": 1}, "attachments": []}
        a = Aggregate.from_dict(d)
        assert a.last_updated is None
        assert a.to_dict()["last_updated"] is None


# ── Channel ───────────────────────────────────────────────────────────


class TestChannel:
    def test_from_dict(self):
        c = Channel.from_dict(CHANNEL_DICT)
        assert c.name == "sensor_data"
        assert c.owner_id == 55555
        assert c.is_private is False
        assert c.aggregate is not None
        assert c.aggregate.data["status"] == "ok"

    def test_to_dict(self):
        c = Channel.from_dict(CHANNEL_DICT)
        d = c.to_dict()
        assert d["name"] == "sensor_data"
        assert "aggregate" in d

    def test_none_aggregate(self):
        d = {**CHANNEL_DICT}
        del d["aggregate"]
        c = Channel.from_dict(d)
        assert c.aggregate is None


# ── EventSubscription ─────────────────────────────────────────────────


class TestEventSubscription:
    def test_all_contains_each(self):
        assert EventSubscription.message_create in EventSubscription.all
        assert EventSubscription.message_update in EventSubscription.all
        assert EventSubscription.aggregate_update in EventSubscription.all
        assert EventSubscription.oneshot_message in EventSubscription.all

    def test_combine(self):
        combined = EventSubscription.message_create | EventSubscription.aggregate_update
        assert EventSubscription.message_create in combined
        assert EventSubscription.aggregate_update in combined
        assert EventSubscription.message_update not in combined


# ── MessageCreateEvent ────────────────────────────────────────────────


class TestMessageCreateEvent:
    def test_from_dict(self):
        d = {
            "id": "1",
            "author_id": "2",
            "channel": CHANNEL_ID_DICT,
            "data": {"hello": "world"},
            "attachments": [],
        }
        e = MessageCreateEvent.from_dict(d)
        assert e.message.id == 1
        assert e.message.author_id == 2
        assert e.channel.name == "test_channel"
        assert e.message.data == {"hello": "world"}


# ── OneShotMessage ────────────────────────────────────────────────────


class TestOneShotMessage:
    def test_is_message_create_subclass(self):
        ch = ChannelID(3, "ch")
        msg = Message.from_dict(
            {
                "id": "1",
                "author_id": "2",
                "channel": ch.to_dict(),
                "data": {},
                "attachments": [],
            }
        )
        e = OneShotMessage(ch, msg)
        assert isinstance(e, MessageCreateEvent)

    def test_from_dict(self):
        d = {
            "id": "1",
            "author_id": "2",
            "channel": CHANNEL_ID_DICT,
            "data": {},
            "attachments": [],
        }
        e = OneShotMessage.from_dict(d)
        assert isinstance(e, OneShotMessage)
        assert isinstance(e, MessageCreateEvent)


# ── MessageUpdateEvent ────────────────────────────────────────────────


class TestMessageUpdateEvent:
    def test_from_dict(self):
        d = {
            "channel": CHANNEL_ID_DICT,
            "author_id": 2,
            "organisation_id": 3,
            "message": MESSAGE_DICT,
            "request_data": {"key": "val"},
        }
        e = MessageUpdateEvent.from_dict(d)
        assert e.channel.name == "test_channel"
        assert e.author_id == 2
        assert e.organisation_id == 3
        assert e.message.id == 99999
        assert e.request_data == {"key": "val"}


# ── AggregateUpdateEvent ─────────────────────────────────────────────


class TestAggregateUpdateEvent:
    def test_from_dict(self):
        d = {
            "author_id": 1,
            "channel": CHANNEL_ID_DICT,
            "aggregate": AGGREGATE_DICT,
            "request_data": AGGREGATE_DICT,
            "organisation_id": 99,
        }
        e = AggregateUpdateEvent.from_dict(d)
        assert e.author_id == 1
        assert e.channel.name == "test_channel"
        assert e.aggregate.data["status"] == "ok"
        assert e.organisation_id == 99


# ── DeploymentEvent ───────────────────────────────────────────────────


class TestDeploymentEvent:
    def test_from_dict(self):
        d = {"agent_id": 1, "app_id": 2, "app_install_id": 3}
        e = DeploymentEvent.from_dict(d)
        assert e.agent_id == 1
        assert e.app_id == 2
        assert e.app_install_id == 3


# ── ScheduleEvent ────────────────────────────────────────────────────


class TestScheduleEvent:
    def test_from_dict(self):
        e = ScheduleEvent.from_dict({"schedule_id": 42})
        assert e.schedule_id == 42


# ── IngestionEndpointEvent ───────────────────────────────────────────


class TestIngestionEndpointEvent:
    def test_from_dict_with_parser(self):
        import json

        d = {
            "ingestion_id": 1,
            "agent_id": 2,
            "organisation_id": 3,
            "payload": '{"temp": 22}',
        }
        e = IngestionEndpointEvent.from_dict(d, parser=json.loads)
        assert e.ingestion_id == 1
        assert e.payload == {"temp": 22}


# ── ManualInvokeEvent ────────────────────────────────────────────────


class TestManualInvokeEvent:
    def test_from_dict(self):
        d = {"organisation_id": 5, "payload": "run_now"}
        e = ManualInvokeEvent.from_dict(d)
        assert e.organisation_id == 5
        assert e.payload == "run_now"


# ── TurnCredential ───────────────────────────────────────────────────


class TestTurnCredential:
    TURN_DICT = {
        "username": "user1",
        "credential": "pass1",
        "ttl": 3600,
        "expires_at": 1700003600,
        "uris": ["turn:example.com:3478"],
    }

    def test_from_dict(self):
        tc = TurnCredential.from_dict(self.TURN_DICT)
        assert tc.username == "user1"
        assert tc.credential == "pass1"
        assert tc.ttl == 3600
        assert tc.uris == ["turn:example.com:3478"]

    def test_roundtrip_proto(self):
        tc = TurnCredential.from_dict(self.TURN_DICT)
        proto = tc.to_proto()
        tc2 = TurnCredential.from_proto(proto)
        assert tc2.username == tc.username
        assert tc2.credential == tc.credential
        assert tc2.ttl == tc.ttl
        assert tc2.expires_at == tc.expires_at
        assert tc2.uris == tc.uris


# ── ConnectionConfig ─────────────────────────────────────────────────


class TestConnectionConfig:
    def test_from_dict(self):
        d = {
            "connection_type": "Continuous",
            "expected_interval": 60,
            "offline_after": 120,
            "sleep_time": None,
            "next_wake_time": None,
        }
        cc = ConnectionConfig.from_dict(d)
        assert cc.connection_type == ConnectionType.continuous
        assert cc.expected_interval == 60
        assert cc.offline_after == 120

    def test_to_dict(self):
        cc = ConnectionConfig(ConnectionType.periodic, 30, 60, None, None)
        d = cc.to_dict()
        assert d["connection_type"] == "Periodic"
        assert d["expected_interval"] == 30

    def test_equality(self):
        a = ConnectionConfig(ConnectionType.continuous, 60, 120, None, None)
        b = ConnectionConfig(ConnectionType.continuous, 60, 120, None, None)
        c = ConnectionConfig(ConnectionType.periodic, 60, 120, None, None)
        assert a == b
        assert a != c

    def test_from_v1(self):
        d = {
            "connectionType": "constant",
            "connectionPeriod": 60,
            "offlineAfter": 120,
        }
        cc = ConnectionConfig.from_v1(d)
        assert cc.connection_type == ConnectionType.continuous
        assert cc.expected_interval == 60


# ── DooverConnectionStatus ───────────────────────────────────────────


class TestDooverConnectionStatus:
    def test_from_dict(self):
        d = {
            "status": "ContinuousOnline",
            "last_online": 1700000000000,
            "last_ping": 1700000001000,
            "user_agent": "pydoover/1.0",
            "ip": "1.2.3.4",
            "latency_ms": 50,
        }
        cs = DooverConnectionStatus.from_dict(d)
        assert cs.status == ConnectionStatus.continuous_online
        assert cs.user_agent == "pydoover/1.0"
        assert cs.latency_ms == 50

    def test_to_dict_skips_none(self):
        cs = DooverConnectionStatus(
            ConnectionStatus.continuous_online,
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        d = cs.to_dict()
        assert "user_agent" not in d
        assert "ip" not in d
        assert "latency_ms" not in d

    def test_equality(self):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        a = DooverConnectionStatus(ConnectionStatus.continuous_online, dt, dt)
        b = DooverConnectionStatus(ConnectionStatus.continuous_online, dt, dt)
        assert a == b


# ── ConnectionType ────────────────────────────────────────────────────


class TestConnectionType:
    @pytest.mark.parametrize(
        "v1_val, expected",
        [
            ("constant", ConnectionType.continuous),
            ("continuous", ConnectionType.continuous),
            ("periodic", ConnectionType.periodic),
            ("periodic_continuous", ConnectionType.periodic_continuous),
        ],
    )
    def test_from_v1(self, v1_val, expected):
        assert ConnectionType.from_v1(v1_val) == expected

    def test_from_v1_unknown(self):
        with pytest.raises(ValueError):
            ConnectionType.from_v1("unknown_type")


# ── Re-export compatibility ──────────────────────────────────────────


class TestReExports:
    def test_device_agent_models_reexport(self):
        from pydoover.docker.device_agent.models import (
            Aggregate,
            TurnCredential,
        )

        assert Aggregate is not None
        assert TurnCredential is not None

    def test_processor_types_reexport(self):
        from pydoover.cloud.processor.types import (
            AggregateUpdateEvent,
            DeploymentEvent,
        )

        assert AggregateUpdateEvent is not None
        assert DeploymentEvent is not None


# ── Message.timestamp ─────────────────────────────────────────────────


class TestMessageTimestamp:
    def test_timestamp_from_snowflake(self):
        dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        snowflake = generate_snowflake_id_at(dt)
        m = Message(snowflake, 1, ChannelID(1, "ch"), {}, [])
        # should round-trip to within 1 second (snowflake has ms precision, but no sub-ms)
        assert abs((m.timestamp - dt).total_seconds()) < 1


# ── Proto roundtrip with attachments ──────────────────────────────────


class TestProtoWithAttachments:
    def test_aggregate_proto_preserves_attachments(self):
        a = Aggregate(
            data={"key": "value"},
            attachments=[
                Attachment("a.txt", "text/plain", 100, "https://example.com/a.txt"),
                Attachment("b.png", "image/png", 2048, "https://example.com/b.png"),
            ],
            last_updated=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        proto = a.to_proto()
        a2 = Aggregate.from_proto(proto)
        assert len(a2.attachments) == 2
        assert a2.attachments[0].filename == "a.txt"
        assert a2.attachments[1].filename == "b.png"
        assert a2.attachments[1].size == 2048

    def test_message_proto_preserves_attachments(self):
        m = Message(
            id=1,
            author_id=2,
            channel=ChannelID(3, "ch"),
            data={"x": 1},
            attachments=[
                Attachment("file.csv", "text/csv", 512, "https://example.com/file.csv"),
            ],
        )
        proto = m.to_proto()
        m2 = Message.from_proto(proto)
        assert len(m2.attachments) == 1
        assert m2.attachments[0].filename == "file.csv"
        assert m2.attachments[0].content_type == "text/csv"


# ── Event isinstance discrimination ──────────────────────────────────


def _make_event_msg(channel_id=None):
    ch = channel_id or ChannelID(3, "ch")
    return ch, Message.from_dict(
        {
            "id": "1",
            "author_id": "2",
            "channel": ch.to_dict(),
            "data": {},
            "attachments": [],
        }
    )


class TestEventDiscrimination:
    """OneShotMessage must be checked before MessageCreateEvent in isinstance
    chains, since it's a subclass. Verify the type hierarchy works correctly."""

    def test_oneshot_is_message_create(self):
        e = OneShotMessage(*_make_event_msg())
        assert isinstance(e, MessageCreateEvent)

    def test_message_create_is_not_oneshot(self):
        e = MessageCreateEvent(*_make_event_msg())
        assert not isinstance(e, OneShotMessage)

    def test_dispatch_order_matters(self):
        oneshot = OneShotMessage(*_make_event_msg())
        create = MessageCreateEvent(*_make_event_msg())

        # simulates the dispatch pattern in _run_channel_stream
        def classify(event):
            if isinstance(event, OneShotMessage):
                return "oneshot"
            elif isinstance(event, MessageCreateEvent):
                return "create"
            return "unknown"

        assert classify(oneshot) == "oneshot"
        assert classify(create) == "create"


# ── EventSubscription edge cases ─────────────────────────────────────


class TestEventSubscriptionEdgeCases:
    def test_single_flag_not_in_different_flag(self):
        assert (
            EventSubscription.message_create not in EventSubscription.aggregate_update
        )

    def test_all_is_superset_of_any_combination(self):
        combo = EventSubscription.message_create | EventSubscription.oneshot_message
        # every flag in combo should be in all
        for flag in combo:
            assert flag in EventSubscription.all

    def test_empty_flag(self):
        empty = EventSubscription(0)
        assert EventSubscription.message_create not in empty


# ── from_dict robustness ─────────────────────────────────────────────


class TestFromDictRobustness:
    def test_aggregate_missing_attachments_key(self):
        d = {"data": {"x": 1}}
        a = Aggregate.from_dict(d)
        assert a.attachments == []
        assert a.last_updated is None

    def test_message_update_missing_request_data(self):
        d = {
            "channel": CHANNEL_ID_DICT,
            "author_id": 1,
            "organisation_id": 2,
            "message": MESSAGE_DICT,
        }
        e = MessageUpdateEvent.from_dict(d)
        assert e.request_data == {}

    def test_channel_id_coerces_string_agent_id(self):
        ch = ChannelID.from_dict({"agent_id": "999", "name": "test"})
        assert ch.agent_id == 999
        assert isinstance(ch.agent_id, int)

    def test_message_coerces_string_ids(self):
        m = Message.from_dict(MESSAGE_DICT)
        assert isinstance(m.id, int)
        assert isinstance(m.author_id, int)


# ── ConnectionConfig edge cases ──────────────────────────────────────


class TestConnectionConfigEdgeCases:
    def test_from_dict_none_connection_type(self):
        d = {
            "connection_type": None,
            "expected_interval": None,
            "offline_after": None,
            "sleep_time": None,
            "next_wake_time": None,
        }
        cc = ConnectionConfig.from_dict(d)
        assert cc.connection_type is None

    def test_not_equal_to_non_config(self):
        cc = ConnectionConfig(ConnectionType.continuous, 60, 120, None, None)
        assert cc != "not a config"
        assert cc != 42

    def test_doover_connection_status_not_equal_to_non_status(self):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        cs = DooverConnectionStatus(ConnectionStatus.continuous_online, dt, dt)
        assert cs != "not a status"


# ── Channel to_dict edge cases ───────────────────────────────────────


class TestChannelToDict:
    def test_none_aggregate_excluded(self):
        c = Channel("ch", 1, False, None, None, None)
        d = c.to_dict()
        assert "aggregate" not in d

    def test_with_aggregate_included(self):
        agg = Aggregate({"x": 1}, [], None)
        c = Channel("ch", 1, True, None, None, agg)
        d = c.to_dict()
        assert "aggregate" in d
        assert d["aggregate"]["data"] == {"x": 1}
