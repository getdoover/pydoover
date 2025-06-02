# class TestClass:
#     def __init__(self):
#         ## A list of return values simulating a battery voltage with an intermittent drop
#         self.values = (
#             [
#                 12.0,
#                 11.5,
#                 11.0,
#                 10.0,
#                 10.5,
#                 11.0,
#                 11.5,
#                 5,
#                 12.0,
#                 12.5,
#                 13.0,
#                 13.5,
#                 14.0,
#                 14.5,
#                 15.0,
#             ]
#             + [0] * 30
#             + [12] * 25
#             + [None] * 3
#             + [8] * 10
#         )
#
#         ## An alternate list the same as the batteries but negative
#         # self.values = [-v for v in self.values if v is not None]
#
#         ## Another alternate list, but of a much smaller magnitude
#         # self.values = [v/100 for v in self.values if v is not None]
#
#         ## another alternate list, but with a much larger magnitude
#         self.values_2 = [v * 100 for v in self.values if v is not None]
#
#         # ## A list of return values simulating a gas ppm sensor with an intermittent spike
#         # self.values = [
#         #     5000, 4900, 4800, 4700, 4850, 5000, 5150, 5300, 5250, 5200, 5150, 5100, 5050, 5000, 4950, 4900,
#         #     20000, 19500, 19000, 500, 600, 550, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
#         #     5000, 4900, 4800, 4700, 4850, 5000, 5150, 5300, 5250, 5200, 5150, 5100, 5050, 5000, 4950, 4900,
#         #     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         # ]
#
#         self.counter = 0
#
#     ## define a generator function that returns the next sensor value
#     def _next(self):
#         # increment the counter
#         self.counter += 1
#
#     def is_running(self):
#         return self.counter < len(self.values)
#
#     def _raw_sensor_value(self):
#         if self.counter < len(self.values):
#             return self.values[self.counter]
#         return None
#
#     def _raw_sensor_value_2(self):
#         if self.counter < len(self.values):
#             return self.values_2[self.counter]
#         return None
#
#     ## Can optionally provide initial_estimate, initial_error_estimate, and process_variance, among others here also
#     @apply_kalman_filter()
#     def sensor_value(self, kf_process_variance=None):
#         return self._raw_sensor_value()
#
#     @apply_kalman_filter()
#     def sensor_value_2(self):
#         return self._raw_sensor_value_2()
#
#
# logging.basicConfig(level=logging.DEBUG)
#
# test = TestClass()
# # logging.info(f"Raw values: {test.values}")
#
# while test.is_running():
#     filtered_value = test.sensor_value(kf_process_variance=0.001)
#     # filtered_value_2 = test.sensor_value_2()
#     # Can also provide measurement_variance and dt as keyword arguments. e.g.
#     # filtered_value = test.sensor_value(kf_measurement_variance=0.5, kf_dt=1)
#
#     # logging.info(f"Raw value: {test._raw_sensor_value()}, Filtered value: {filtered_value}")
#     test._next()
#     time.sleep(1)
