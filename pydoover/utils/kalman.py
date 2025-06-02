#!/usr/bin/env python3

import time
import logging


## A simple 1D Kalman filter implementation
## This filter is designed to be used with a single sensor reading (e.g., a voltage reading, a temperature reading, etc.)
## It includes automatic time step calculation based on the time since the last update, however this can be overridden by providing a dt parameter.
## Has some basic outlier detection and handling

## If you want to adjust the overall sensitivity of the filter, you can adjust the process_variance parameter.
## Default is 0.5, which is a good starting point for most applications. 1 will make the filter more sensitive to changes, 0.1 will make it less sensitive.

## If you want to adjust the sensitivity to outliers, you can adjust the outlier_threshold which defaults to 5.
## Increase this value to make the filter less sensitive to outliers.

## If you are not familiar with Kalman filters, here is a good resource:
## https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/


class KalmanFilter1D:
    def __init__(
        self,
        initial_estimate=None,
        initial_error_estimate=None,
        process_variance=None,
        outlier_protection=None,
        outlier_threshold=None,
        outlier_variance_multiplier=None,
    ):
        self.debug = False

        self.default_process_variance = 0.5  # Default process variance if not provided
        self.default_initial_estimate_ratio = 25  # The ratio of the initial estimate variance to the first measurement variance
        self.default_measurement_variance = (
            0.5  # Default measurement variance if not provided
        )

        self.outlier_protection = (
            outlier_protection if outlier_protection is not None else True
        )  # Whether to use outlier protection
        self.default_outlier_threshold = (
            5  # The threshold for an outlier (in multiples of the error estimate)
        )
        self.default_outlier_variance_multiplier = (
            25  # Multiplier for the measurement variance for an outlier
        )

        self.estimate = initial_estimate  # Initial estimate (x_hat)
        self.error_estimate = initial_error_estimate  # Initial error estimate (P)
        self.process_variance = (
            process_variance or self.default_process_variance
        )  # Process variance (Q)

        self.outlier_threshold = (
            outlier_threshold or self.default_outlier_threshold
        )  # Threshold for an outlier
        self.outlier_variance_multiplier = (
            outlier_variance_multiplier or self.default_outlier_variance_multiplier
        )

        self.kalman_gain = 0  # Kalman gain (K)
        self.last_timestamp = None  # To store the last time the filter was updated
        self.enabled = True

    def set_estimate(self, estimate):
        self.estimate = estimate

    def set_error_estimate(self, error_estimate):
        self.error_estimate = error_estimate

    def set_process_variance(self, process_variance):
        self.process_variance = process_variance

    def set_outlier_protection(self, outlier_protection):
        self.outlier_protection = outlier_protection

    def set_outlier_threshold(self, outlier_threshold):
        self.outlier_threshold = outlier_threshold

    def set_outlier_variance_multiplier(self, outlier_variance_multiplier):
        self.outlier_variance_multiplier = outlier_variance_multiplier

    def update(
        self,
        measurement,
        measurement_variance=None,
        dt=None,
        outlier_protection=None,
        process_variance=None,
    ):
        if self.enabled is False:
            # allow a way of disabling kalman filter in test mode.
            return measurement

        if process_variance is not None:
            if self.debug:
                logging.debug(f"Setting process variance to {process_variance}")
            self.process_variance = process_variance

        ## If the measurement is None, return the last estimate
        if measurement is None:
            return self.estimate

        ## If the measurement variance is not provided, set it to the default
        measurement_variance = measurement_variance or self.default_measurement_variance

        ## If not initialized, set the initial estimate to the first measurement
        if self.error_estimate is None:
            if self.debug:
                logging.debug("Initializing Kalman filter")
            self.error_estimate = (
                measurement_variance * self.default_initial_estimate_ratio
            )
        if self.estimate is None:
            self.estimate = measurement
            self.last_timestamp = time.time()
            return self.estimate

        current_time = time.time()
        # If dt is not provided, calculate it based on the time since the last update
        if dt is None:
            if self.last_timestamp is None:
                dt = 1  # Default to 1 second if this is the first call
            else:
                dt = current_time - self.last_timestamp
        self.last_timestamp = current_time

        # If the measurement is an outlier, increase the measurement variance
        outlier_protection = (
            outlier_protection
            if outlier_protection is not None
            else self.outlier_protection
        )
        outlier_message = None
        if (
            outlier_protection
            and abs(measurement - self.estimate)
            > self.outlier_threshold * self.error_estimate
        ):
            # logging.debug(f"Outlier detected: {measurement} (threshold: {self.outlier_threshold * self.error_estimate})")
            outlier_message = f"Outlier detected: {measurement} (threshold: {self.outlier_threshold * self.error_estimate})"
            measurement_variance *= self.outlier_variance_multiplier

        # Adjust process variance with dt
        adjusted_process_variance = self.process_variance * dt

        # Also adjust the process variance based on the magnitude of the measurement. This makes the filter more performant over datasets of wider magnitude.
        # adjusted_process_variance = self.process_variance * (1 + (abs(measurement) / 10)) ## This is a good starting point for most applications

        # Prediction step
        self.error_estimate += adjusted_process_variance

        # Update step
        if (self.error_estimate + measurement_variance) == 0:
            ## If the error estimate + measurement variance is 0, avoid division by zero
            self.kalman_gain = self.error_estimate / 0.0001
        else:
            self.kalman_gain = self.error_estimate / (
                self.error_estimate + measurement_variance
            )
        self.estimate += self.kalman_gain * (measurement - self.estimate)
        self.error_estimate = (1 - self.kalman_gain) * self.error_estimate

        debug_output = f"Measurement: {measurement}, Estimate: {self.estimate}, Error estimate: {self.error_estimate}"
        if outlier_message:
            debug_output += f" | {outlier_message}"
        if self.debug:
            logging.debug(debug_output)

        return self.estimate


def apply_kalman_filter(
    initial_estimate=None,
    initial_error_estimate=None,
    process_variance=None,
    outlier_protection=None,
    outlier_threshold=None,
    outlier_variance_multiplier=None,
):
    """A decorator to apply a Kalman filter to the return value of a function
    The function should return a single value (e.g., a sensor reading)
    See below for an example of how to use this decorator

    Parameters
    ----------
    initial_estimate
    initial_error_estimate
    process_variance
    outlier_protection
    outlier_threshold
    outlier_variance_multiplier

    Returns
    -------

    """

    def decorator(func):
        ## Generate an id for the Kalman filter instance
        kf_id = id(func)

        def wrapper(self, *args, **kwargs):
            ## Instantiate the Kalman filter if it doesn't exist
            ## This allows multiple instances of the same function to have separate Kalman filters
            if not hasattr(self, "_kf_instances"):
                self._kf_instances = {}
            if kf_id not in self._kf_instances:
                # Create an instance of the Kalman filter with the provided parameters
                self._kf_instances[kf_id] = KalmanFilter1D(
                    initial_estimate=initial_estimate,
                    initial_error_estimate=initial_error_estimate,
                    process_variance=process_variance,
                    outlier_protection=outlier_protection,
                    outlier_threshold=outlier_threshold,
                    outlier_variance_multiplier=outlier_variance_multiplier,
                )

            _kalman_filter = self._kf_instances[kf_id]

            wrapper._kalman_filter = _kalman_filter

            # Call the original function and get its return value
            result = func(self, *args, **kwargs)

            # Extract measurement_variance and optional dt from kwargs or set defaults
            measurement_variance = kwargs.pop("kf_measurement_variance", None)
            dt = kwargs.pop("kf_dt", None)  # Allow dt to be optionally overridden
            measurement_outlier_protection = kwargs.pop(
                "kf_outlier_protection", None
            )  # Allow outlier_protection to be optionally overridden
            kf_process_variance = kwargs.pop(
                "kf_process_variance", None
            )  # Allow process_variance to be optionally overridden

            # Apply the Kalman filter to the return value
            filtered_result = _kalman_filter.update(
                result,
                measurement_variance,
                dt,
                measurement_outlier_protection,
                kf_process_variance,
            )
            return filtered_result

        return wrapper

    return decorator


def apply_async_kalman_filter(
    initial_estimate=None,
    initial_error_estimate=None,
    process_variance=None,
    outlier_protection=None,
    outlier_threshold=None,
    outlier_variance_multiplier=None,
):
    def decorator(func):
        ## Generate an id for the Kalman filter instance
        kf_id = id(func)

        async def wrapper(self, *args, **kwargs):
            ## Instantiate the Kalman filter if it doesn't exist
            ## This allows multiple instances of the same function to have separate Kalman filters
            if not hasattr(self, "_kf_instances"):
                self._kf_instances = {}
            if kf_id not in self._kf_instances:
                # Create an instance of the Kalman filter with the provided parameters
                self._kf_instances[kf_id] = KalmanFilter1D(
                    initial_estimate=initial_estimate,
                    initial_error_estimate=initial_error_estimate,
                    process_variance=process_variance,
                    outlier_protection=outlier_protection,
                    outlier_threshold=outlier_threshold,
                    outlier_variance_multiplier=outlier_variance_multiplier,
                )

            _kalman_filter = self._kf_instances[kf_id]

            wrapper._kalman_filter = _kalman_filter

            # Call the original function and get its return value
            result = await func(self, *args, **kwargs)

            # Extract measurement_variance and optional dt from kwargs or set defaults
            measurement_variance = kwargs.pop("kf_measurement_variance", None)
            dt = kwargs.pop("kf_dt", None)  # Allow dt to be optionally overridden
            measurement_outlier_protection = kwargs.pop(
                "kf_outlier_protection", None
            )  # Allow outlier_protection to be optionally overridden
            kf_process_variance = kwargs.pop(
                "kf_process_variance", None
            )  # Allow process_variance to be optionally overridden

            # Apply the Kalman filter to the return value
            filtered_result = _kalman_filter.update(
                result,
                measurement_variance,
                dt,
                measurement_outlier_protection,
                kf_process_variance,
            )
            return filtered_result

        return wrapper

    return decorator
