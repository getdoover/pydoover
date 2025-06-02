from pathlib import Path

from pydoover import config


class SampleConfig(config.ApplicationConfig):
    def __init__(self):
        # these 2 are device specific, and inherit from the device-set variables.
        # However, the user can override them if they wish.

        self.num_di = config.Integer(
            "Digital Input Count",
            default=config.Variable("device", "digitalInputCount"),
            min_val=0,
        )
        self.num_do = config.Integer(
            "Digital Output Count",
            default=config.Variable("device", "digitalOutputCount"),
            min_val=0,
        )

        self.outputs_enabled = config.Boolean("Digital Outputs Enabled", default=True)
        self.funny_message = config.String(
            "A Funny Message"
        )  # this will be required as no default given.


if __name__ == "__main__":
    c = SampleConfig()
    c.export(Path("app_config.json"))
