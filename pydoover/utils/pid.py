import time


class PID:
    def __init__(self, Kp, Ki, Kd, setpoint=0, output_limits=(None, None)):
        """
        Initialize the PID controller.

        :param Kp: Proportional gain
        :param Ki: Integral gain
        :param Kd: Derivative gain
        :param setpoint: The target value that the PID controller tries to achieve
        :param output_limits: Tuple (min_output, max_output) for limiting output
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.output_limits = output_limits

        self._last_time = None
        self._last_error = None
        self._integral = 0
        self._last_output = 0

    def update(self, feedback_value, dt=None):
        """
        Update the PID loop with the current feedback value.

        :param feedback_value: The current value from the process
        :param dt: Optional time interval. If not provided, it's calculated internally.
        :return: The control output
        """
        current_time = time.time()
        error = self.setpoint - feedback_value

        if self._last_time is None:
            # First call, just initialize and return 0
            self._last_time = current_time
            self._last_error = error
            if self._last_output is not None:
                return self._last_output
            return 0

        # Calculate time difference (dt) if not provided
        if dt is None:
            delta_time = current_time - self._last_time
        else:
            delta_time = dt

        # Ensure we don't update too frequently
        if delta_time <= 0.0:
            return self._last_output

        # Proportional term
        proportional = self.Kp * error

        # Integral term
        self._integral += error * delta_time
        integral = self.Ki * self._integral

        # Derivative term
        delta_error = error - self._last_error
        derivative = self.Kd * (delta_error / delta_time)

        # Compute the output
        output = proportional + integral + derivative

        # Limit the output to specified limits
        min_output, max_output = self.output_limits
        if min_output is not None:
            output = max(min_output, output)
        if max_output is not None:
            output = min(max_output, output)

        # Store values for the next loop iteration
        self._last_output = output
        self._last_time = current_time
        self._last_error = error

        return output

    def set_output_limits(self, min_output, max_output):
        """
        Set the minimum and maximum output limits.

        :param min_output: Minimum limit
        :param max_output: Maximum limit
        """
        self.output_limits = (min_output, max_output)

    def set_setpoint(self, setpoint):
        """
        Set a new target value for the PID to reach.

        :param setpoint: The target value
        """
        self.setpoint = setpoint

    def set_last_output(self, output):
        """
        Set the last output value.

        :param output: The last output value
        """
        self._last_output = output

    def set_last_error(self, error):
        """
        Set the last error value.

        :param error: The last error value
        """
        self._last_error = error

    def set_integral_output(self, integral_output):
        """
        Initialise the integral output for a desired output value.

        :param integral: The integral integral_output value
        """
        if self.Ki == 0:
            self._integral = 0
        else:
            self._integral = integral_output / self.Ki

    def reset(self):
        """
        Reset the internal state of the PID controller.
        """
        self._last_time = None
        self._last_error = None
        self._integral = 0
        self._last_output = 0
