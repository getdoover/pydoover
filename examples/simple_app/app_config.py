from pathlib import Path

from pydoover import config


class SampleConfig(config.Schema):
    # These 2 are device specific, and inherit from the device-set variables.
    # However, the user can override them if they wish.
    num_di = config.Integer(
        "Digital Input Count",
        default=config.Variable("device", "digitalInputCount"),
        minimum=0,
    )
    num_do = config.Integer(
        "Digital Output Count",
        default=config.Variable("device", "digitalOutputCount"),
        minimum=0,
    )
    outputs_enabled = config.Boolean("Digital Outputs Enabled", default=True)
    funny_message = config.String("A Funny Message")


if __name__ == "__main__":
    SampleConfig().export(Path("app_config.json"), "sample_app")
