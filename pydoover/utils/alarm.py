#!/usr/bin/env python3

import time
import logging
import asyncio

## A generic alarm class that can be used to trigger things via a callback function when a threshold is met
## threshold can be greater than or less than a specified value

## Uses grace_period and min_inter_alarm to prevent rapid triggering of the alarm
## If threshold is met, the alarm will trigger and the callback will be called

## Grace period is the amount of time which the threshold has to be met before the alarm is triggered again
## Min inter alarm is the minimum time between alarms
log = logging.getLogger(__name__)


class Alarm:
    def __init__(
        self,
        threshold_met,
        callback=None,
        grace_period=None,
        min_inter_alarm=None,
    ):
        self.default_grace_period = 60 * 60  # an hour
        self.default_min_inter_alarm = 60 * 60 * 24  # a day

        self.threshold_met = threshold_met
        self.callback = callback
        self.grace_period = grace_period or self.default_grace_period
        self.min_inter_alarm = min_inter_alarm or self.default_min_inter_alarm

        self.last_alarm_time = None
        self.initial_trigger_time = None

    async def check_value(
        self,
        value,
        threshold_met,
        grace_period=None,
        min_inter_alarm=None,
    ):
        if grace_period is not None:
            self.grace_period = grace_period

        if min_inter_alarm is not None:
            self.min_inter_alarm = min_inter_alarm

        if self.threshold_met(value) is False:
            log.debug(f"Threshold not met: {value}")
            self.initial_trigger_time = None
            return False

        else:
            log.debug(f"Threshold met: {value}")
            if self._check_grace_period():
                log.debug(f"Grace period met: {value}")
                if self._check_min_inter_alarm():
                    log.debug(f"Min inter alarm met: {value}")
                    await self._trigger_alarm()
                else:
                    log.debug(f"Min inter alarm not met: {value}")
            else:
                log.debug(f"Grace period not met: {value}")

    def _check_grace_period(self):
        if self.initial_trigger_time is None:
            self.initial_trigger_time = time.time()
            return False

        else:
            if self.initial_trigger_time + self.grace_period < time.time():
                return True
            else:
                return False

    def _check_min_inter_alarm(self):
        if self.last_alarm_time is None:
            return True
        else:
            if self.last_alarm_time + self.min_inter_alarm < time.time():
                return True
            else:
                return False

    async def _trigger_alarm(self):
        if self.callback:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback()
            else:
                self.callback()
        self.last_alarm_time = time.time()

    def reset_alarm(self):
        self.last_alarm_time = None
        self.initial_trigger_time = None


def create_alarm(
    func,
    threshold_met,
    callback=None,
    grace_period=None,
    min_inter_alarm=None,
):
    """A decorator to check an alarm against the return value of a function
    The function will fire the inputted callback if the alarm is triggered
    See below for an example of how to use this decorator

    Parameters
    ----------
    threshold_met
    callback
    grace_period
    min_inter_alarm

    Returns
    -------

    Example
    -------

        self.get_test_increment = create_alarm(
            self.get_test_increment,
            lambda x:x>20,
            callback=self.test_alarm_callback,
            grace_period=15,
            min_inter_alarm=60,
        )

    async def get_test_increment(self):
        return self.test_increment


    in the above case, the alarm will be checked each time the get_test_increment method is called
    if the value returned is greater than 20 for at least 15 seconds, the callback will be called
    the callback will be called at most once every 60 seconds
    """

    alarm = Alarm(
        threshold_met=threshold_met,
        callback=callback,
        grace_period=grace_period,
        min_inter_alarm=min_inter_alarm,
    )

    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        await alarm.check_value(result, threshold_met)

        return result

    wrapper.alarm = alarm

    return wrapper
