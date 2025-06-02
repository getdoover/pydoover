# # async def run_test():
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG)
#
#     iface = modbus_iface()
#     iface.open_bus(
#         bus_type="serial",
#         name="test",
#         serial_port="/dev/ttyk37simOut",
#         serial_baud=38400,
#         serial_method="rtu",
#         serial_bits=8,
#         serial_parity="N",
#         serial_stop=1,
#         serial_timeout=0.3,
#     )
#
#     print(iface.getBusStatus(bus_id="test"))
#
#     result = iface.read_registers(
#         bus_id="test",
#         modbus_id=1,
#         start_address=0,
#         num_registers=23,
#     )
#     print(result)
#
#     watchdog = result[22] + 1
#
#     result = iface.write_registers(
#         bus_id="test",
#         modbus_id=1,
#         start_address=22,
#         values=[watchdog],
#     )
#
#     ## define a function to print the results of read register subscription
#     def print_results(values):
#         print(values)
#
#     loop = asyncio.get_event_loop()
#
#     ## add a read register subscription
#     iface.add_read_register_subscription(
#         bus_id="test",
#         modbus_id=1,
#         start_address=0,
#         num_registers=23,
#         callback=print_results,
#     )
#
#     print("Subscribed to read register subscription")
#
#     ## add a read register subscription
#     iface.add_read_register_subscription(
#         bus_id="test",
#         modbus_id=1,
#         start_address=0,
#         num_registers=10,
#         callback=print_results,
#     )
#
#     # async def run_test():
#     #     await asyncio.sleep(20)
#     #     iface.close()
#
#     try:
#         asyncio.get_event_loop().run_forever()
#     except KeyboardInterrupt:
#         pass
#
#     log.info("Closing modbus interface")
#     # iface.close()
