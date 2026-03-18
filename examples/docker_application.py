import logging
import random
import time

from pydoover.docker import Application, run_app
from pydoover.config import Schema
from pydoover import ui
from pydoover.tags import Tag, Tags


log = logging.getLogger(__name__)

# UI Will look like this

# Variable : Is Working : Bool
# Variable : Uptime : Int
# Parameter : Test Message
# Variable : Test Output
# Action : Send this text as an alert
# Submodule :
#      Variable : Battery Voltage
#      Parameter : Low Battery Voltage Alert
#            Once below this setpoint, send a text and show a warning
#      StateCommand : Charge Battery Mode
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
        "is_working",
        "We Working?",
        curr_val=HelloWorldTags.is_working,
    )
    uptime = ui.NumericVariable(
        "uptime",
        "Uptime",
        curr_val=HelloWorldTags.uptime,
    )
    send_alert = ui.Action("send_alert", "Send message as alert", position=1)
    test_message = ui.TextParameter("test_message", "Put in a message")
    test_output = ui.TextVariable(
        "test_output",
        "This is message we got",
        curr_val=HelloWorldTags.test_output,
    )
    battery = ui.Submodule(
        "battery",
        "Battery Module",
        children=[
            ui.NumericVariable(
                "battery_voltage",
                "Battery Voltage",
                curr_val=HelloWorldTags.battery_voltage,
                precision=2,
                ranges=[
                    ui.Range("Low", 0, 10, ui.Colour.red),
                    ui.Range("Normal", 10, 20, ui.Colour.green),
                    ui.Range("High", 20, 30, ui.Colour.blue),
                ],
            ),
            ui.NumericParameter("low_voltage_alert", "Low Voltage Alert"),
            ui.StateCommand(
                "charge_mode",
                "Charge Mode",
                user_options=[
                    ui.Option("charge", "Charge"),
                    ui.Option("discharge", "Discharge"),
                    ui.Option("idle", "Idle"),
                ],
            ),
        ],
    )


class HelloWorld(Application):
    tags_class = HelloWorldTags
    ui_class = HelloWorldUI

    started: time.time

    def setup(self):
        self.started = time.time()

    def main_loop(self):
        self.tags.is_working.set(True)
        self.tags.uptime.set(time.time() - self.started)
        self.tags.battery_voltage.set(random.randint(900, 2100) / 100)

    @ui.callback("send_alert")
    def on_send_alert(self, command, _new_value):
        output = self.tags.test_output.get()
        log.info("Sending alert: %s", output)
        self.send_notification(output, record_activity=True)
        command.coerce(None)

    @ui.callback("test_message")
    def on_text_parameter_change(self, _command, new_value):
        log.info("New value for test message: %s", new_value)
        self.tags.test_output.set(new_value)

    @ui.callback("charge_mode")
    def on_state_command(self, _command, new_value):
        log.info("New value for state command: %s", new_value)


if __name__ == "__main__":
    new_app = HelloWorld(config=Schema())
    run_app(new_app)
