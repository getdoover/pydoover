import logging
import random
import time

from pydoover.docker import Application, run_app
from pydoover.config import Schema
from pydoover import ui
from pydoover.models import NotificationSeverity
from pydoover.tags import Tag, Tags


log = logging.getLogger(__name__)

# UI Will look like this

# Variable : Is Working : Bool
# Variable : Uptime : Int
# Parameter : Test Message
# Variable : Test Output
# Button : Send this text as an alert
# Submodule :
#      Variable : Battery Voltage
#      Parameter : Low Battery Voltage Alert
#            Once below this setpoint, send a notification and show a warning
#      Select : Charge Battery Mode
#           - Charge
#           - Discharge
#           - Idle


class HelloWorldTags(Tags):
    is_working = Tag("boolean", default=False)
    uptime = Tag("number", default=0)
    test_output = Tag("string", default="")
    battery_voltage = Tag("number", default=0)


class HelloWorldUI(ui.UI):
    is_working = ui.BooleanVariable(
        "We Working?",
        value=HelloWorldTags.is_working,
    )
    uptime = ui.NumericVariable(
        "Uptime",
        value=HelloWorldTags.uptime,
        units="s",
        precision=0,
    )
    # `name` is what handlers and `ui_manager.get_value()` refer to. Without
    # it the name is derived from the display name, so renaming a label would
    # quietly unhook the handler — always name anything you reference in code.
    send_alert = ui.Button("Send message as alert", name="send_alert", position=1)
    test_message = ui.TextInput("Put in a message", name="test_message")
    test_output = ui.TextVariable(
        "This is message we got",
        value=HelloWorldTags.test_output,
    )
    low_battery_warning = ui.WarningIndicator(
        "Battery voltage is low",
        name="low_battery_warning",
        hidden=True,
    )
    battery = ui.Submodule(
        "Battery Module",
        children=[
            ui.NumericVariable(
                "Battery Voltage",
                value=HelloWorldTags.battery_voltage,
                precision=2,
                ranges=[
                    ui.Range("Low", 0, 10, ui.Colour.red),
                    ui.Range("Normal", 10, 20, ui.Colour.green),
                    ui.Range("High", 20, 30, ui.Colour.blue),
                ],
            ),
            ui.FloatInput("Low Voltage Alert", name="low_voltage_alert", default=10),
            ui.Select(
                "Charge Mode",
                name="charge_mode",
                options=[
                    ui.Option("Charge"),
                    ui.Option("Discharge"),
                    ui.Option("Idle"),
                ],
            ),
        ],
    )


class HelloWorld(Application):
    config_cls = Schema
    tags_cls = HelloWorldTags
    ui_cls = HelloWorldUI

    tags: HelloWorldTags
    ui: HelloWorldUI

    started: float

    async def setup(self):
        self.started = time.time()
        # Only notify on the transition into a low battery, not every loop.
        self.battery_was_low = False

    async def main_loop(self):
        await self.tags.is_working.set(True)
        await self.tags.uptime.set(time.time() - self.started)

        voltage = random.randint(900, 2100) / 100
        await self.tags.battery_voltage.set(voltage)
        await self.check_battery(voltage)

    async def check_battery(self, voltage: float):
        setpoint = self.ui_manager.get_value("low_voltage_alert")
        if setpoint is None:
            return

        is_low = voltage < setpoint
        self.ui.low_battery_warning.hidden = not is_low

        # Edge-triggered: fire once on the way down, and re-arm on the way up.
        if is_low and not self.battery_was_low:
            await self.send_notification(
                f"Battery voltage is {voltage:.2f}V, below the {setpoint}V setpoint",
                title="Low battery",
                severity=NotificationSeverity.Warn,
                event="low-battery",
            )
        self.battery_was_low = is_low

    @ui.handler("send_alert")
    async def on_send_alert(self, ctx, _value):
        # Buttons report the press by setting a value, so clear it to re-arm.
        await ctx.set_value(None)

        message = self.tags.test_output.get()
        if not message:
            log.info("Nothing to send — set a message first")
            return

        log.info("Sending alert: %s", message)
        await self.send_notification(message, title="Alert")

    @ui.handler("test_message")
    async def on_text_parameter_change(self, _ctx, new_value):
        log.info("New value for test message: %s", new_value)
        await self.tags.test_output.set(new_value)

    @ui.handler("charge_mode")
    async def on_charge_mode_change(self, _ctx, new_value):
        log.info("New value for charge mode: %s", new_value)


if __name__ == "__main__":
    new_app = HelloWorld()
    run_app(new_app)
