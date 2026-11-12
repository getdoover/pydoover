"""Intervals are measured on the monotonic clock, not the wall clock.

A Doovit boots with its clock set from an RTC that can be minutes out, and the
first NTP sync then steps the wall clock. With ``time.time()`` a step back of
1373 s froze every app's main loop for 1374 s (Station 1, 2026-11-11).
"""

import asyncio
from collections import deque
from types import SimpleNamespace

import pytest

import pydoover.docker.application as application_module
import pydoover.tags.manager as tags_manager_module
import pydoover.utils.alarm as alarm_module
import pydoover.utils.kalman as kalman_module
import pydoover.utils.pid as pid_module
from pydoover.docker.application import Application
from pydoover.tags.manager import TagsManagerDocker
from pydoover.utils.alarm import Alarm
from pydoover.utils.kalman import KalmanFilter1D
from pydoover.utils.pid import PID

NTP_STEP = 1373.0


class FakeClock:
    """``mono`` is the monotonic clock; the wall clock is ``mono`` plus an
    offset that :meth:`step_wall` moves, the way an NTP step does."""

    def __init__(self, start: float = 1_000.0):
        self.mono = start
        self.wall_offset = 1_700_000_000.0

    def advance(self, seconds: float):
        self.mono += seconds

    def step_wall(self, seconds: float):
        self.wall_offset += seconds

    def module(self):
        return SimpleNamespace(
            time=lambda: self.mono + self.wall_offset,
            monotonic=lambda: self.mono,
        )


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    for module in (
        application_module,
        tags_manager_module,
        alarm_module,
        pid_module,
        kalman_module,
    ):
        monkeypatch.setattr(module, "time", c.module())
    return c


def _bare_application():
    app = Application.__new__(Application)
    app._last_interval_time = None
    app._last_loop_time_warning = None
    app._loop_times = deque(maxlen=20)
    return app


def test_wait_for_interval_ignores_a_wall_clock_step(clock, monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(application_module.asyncio, "sleep", fake_sleep)
    app = _bare_application()

    asyncio.run(app.wait_for_interval(1.0))
    assert slept == [0.5]  # half a period on the first call

    clock.advance(0.3)
    clock.step_wall(-NTP_STEP)
    asyncio.run(app.wait_for_interval(1.0))
    assert slept[-1] == pytest.approx(0.7)

    clock.advance(0.2)
    clock.step_wall(+NTP_STEP)
    asyncio.run(app.wait_for_interval(1.0))
    assert slept[-1] == pytest.approx(0.8)

    assert max(slept) <= 1.0


def test_pid_dt_ignores_a_wall_clock_step(clock):
    pid = PID(Kp=0.0, Ki=0.0, Kd=1.0, setpoint=0.0)
    pid.update(0.0)
    clock.advance(1.0)
    clock.step_wall(-NTP_STEP)
    # error went 0 -> -1 over 1 s: derivative -1, not ~0 or a sign flip.
    assert pid.update(1.0) == pytest.approx(-1.0)


def test_kalman_dt_ignores_a_wall_clock_step(clock):
    f = KalmanFilter1D()
    f.update(10.0)
    clock.advance(1.0)
    clock.step_wall(-NTP_STEP)
    f.update(10.0)
    assert f.last_timestamp == clock.mono


def test_alarm_grace_period_ignores_a_wall_clock_step(clock):
    fired: list[bool] = []
    alarm = Alarm(
        threshold_met=lambda v: v > 5,
        callback=lambda: fired.append(True),
        grace_period=60,
        min_inter_alarm=600,
    )
    asyncio.run(alarm.check_value(10, None))
    clock.advance(10)
    clock.step_wall(+NTP_STEP)  # a step forward must not end the grace early
    asyncio.run(alarm.check_value(10, None))
    assert fired == []
    clock.advance(60)
    asyncio.run(alarm.check_value(10, None))
    assert fired == [True]
    clock.advance(10)
    clock.step_wall(+NTP_STEP)  # nor cut the gap between alarms short
    asyncio.run(alarm.check_value(10, None))
    assert fired == [True]


def test_first_tag_log_flushes_straight_away(clock, monkeypatch):
    """Monotonic time can be small just after boot; the first log must not
    wait for ``tag_log_interval`` to pass since an arbitrary zero."""
    clock.mono = 5.0
    manager = TagsManagerDocker(client=None, tag_log_interval=60)
    flushed: list[bool] = []

    async def noop():
        return None

    async def flush_logs(timestamp=None):
        flushed.append(True)
        manager._last_tag_log_time = clock.mono
        manager._pending_tag_log = {}

    monkeypatch.setattr(manager, "flush_tags", noop)
    monkeypatch.setattr(manager, "flush_live_tags", noop)
    monkeypatch.setattr(manager, "flush_logs", flush_logs)

    manager._pending_tag_log = {"a": 1}
    asyncio.run(manager.commit_tags())
    assert flushed == [True]

    manager._pending_tag_log = {"a": 2}
    clock.advance(30)
    clock.step_wall(+NTP_STEP)
    asyncio.run(manager.commit_tags())
    assert flushed == [True]  # still inside the interval
    clock.advance(31)
    asyncio.run(manager.commit_tags())
    assert flushed == [True, True]
