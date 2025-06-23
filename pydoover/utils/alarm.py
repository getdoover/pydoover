#!/usr/bin/env python3

import time
import logging

## A generic alarm class that can be used to trigger things via a callback function when a threshold is met
## threshold can be greater than or less than a specified value

## Uses grace_period and min_inter_alarm to prevent rapid triggering of the alarm
## If threshold is met, the alarm will trigger and the callback will be called

## Grace period is the amount of time which the threshold has to be met before the alarm is triggered again
## Min inter alarm is the minimum time between alarms


class Alarm:
    def __init__(
        self,
        threshold=None,
        callback=None,
        direction=None,
        grace_period=None,
        min_inter_alarm=None,
    ):
        self.debug = False
        
        self.default_direction = "greater_than"
        self.default_grace_period = 60 * 60 #an hour
        self.default_min_inter_alarm = 60 * 60 * 24 #a day

        self.threshold = threshold
        self.callback = callback
        self.direction = direction or self.default_direction
        self.grace_period = grace_period or self.default_grace_period
        self.min_inter_alarm = min_inter_alarm or self.default_min_inter_alarm

        self.last_alarm_time = None
        self.initial_trigger_time = None

    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_callback(self, callback):
        self.callback = callback
        
    def set_direction(self, direction):
        self.direction = direction

    def set_grace_period(self, grace_period):
        self.grace_period = grace_period

    def set_min_inter_alarm(self, min_inter_alarm):
        self.min_inter_alarm = min_inter_alarm
        
    def check_value(
        self,
        value,
        threshold=None,
        direction=None,
        grace_period=None,
        min_inter_alarm=None,
    ):
        if threshold is not None:
            self.threshold = threshold

        if direction is not None:
            self.direction = direction

        if grace_period is not None:
            self.grace_period = grace_period

        if min_inter_alarm is not None:
            self.min_inter_alarm = min_inter_alarm

        if self._threshold_met(value) is False:
            self.initial_trigger_time = None
            return False
        
        else:
            if self._check_grace_period() and self._check_min_inter_alarm():
                self._trigger_alarm()

    def _threshold_met(self, value):
        if self.direction == "greater_than":
            if value > self.threshold:
                return True
        elif self.direction == "less_than":
            if value < self.threshold:
                return True
        return False

    def _check_grace_period(self):

        if self.initial_trigger_time is None:
            self.initial_trigger_time = time.time()
            return False

        else:
            self.initial_trigger_time + self.grace_period < time.time():
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

    def _trigger_alarm(self):
        self.callback()
        self.last_alarm_time = time.time()

    def reset_alarm(self):
        self.last_alarm_time = None
        self.initial_trigger_time = None


def check_alarm(
    self,
    value,
    threshold=None,
    callback=None,
    direction=None,
    grace_period=None,
    min_inter_alarm=None,
):

    """A decorator to check an alarm against the return value of a function
    The function will fire the inputted callback if the alarm is triggered
    See below for an example of how to use this decorator

    Parameters
    ----------
    threshold
    callback
    direction
    grace_period

    Returns
    -------
    """

    def decorator(func):
        ## Generate an id for the alarm instance
        alarm_id = id(func)

        async def wrapper(*args, **kwargs):
            ## Instantiate the alarm if it doesn't exist
            ## This allows multiple instances of the same function to have separate alarms
            if not hasattr(self, "_alarm_instances"):
                self._alarm_instances = {}
            if alarm_id not in self._alarm_instances:
                self._alarm_instances[alarm_id] = Alarm(
                    threshold=threshold,
                    callback=callback,
                    direction=direction,
                    grace_period=grace_period,
                    min_inter_alarm=min_inter_alarm,
                )

            _alarm = self._alarm_instances[alarm_id]

            wrapper._alarm = _alarm

            result = await func(self, *args, **kwargs)

            _alarm.check_value(result)

            return result

        return wrapper

    return decorator