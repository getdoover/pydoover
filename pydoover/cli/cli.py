import argparse
import inspect
import traceback

import logging
import os
import sys

from .sub_section import SubSection


class CLI:
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="pydoover", description="Interact with running gRPC servers."
        )
        parser.set_defaults(callback=parser.print_help)

        self.subparser = parser.add_subparsers(dest="subcommand", title="Subcommands")
        self.added_subsections = []

        # to stop circular imports...
        try:
            # fixme: make a [docker] extra feature / package which processors can choose not to install.
            from ..docker.platform import PlatformInterface
            from ..docker.device_agent import DeviceAgentInterface
            from ..docker.modbus import ModbusInterface
        except ImportError as e:
            print(e)
            print(
                "Docker interfaces not found. GRPC CLI support will not be available."
            )
        else:
            self.add_grpc_subsection(
                SubSection(
                    PlatformInterface,
                    name="platform",
                    description="Interact with a running Platform Interface container",
                )
            )
            self.add_grpc_subsection(
                SubSection(
                    DeviceAgentInterface,
                    name="device_agent",
                    description="Interact with a running Device Agent container",
                )
            )
            self.add_grpc_subsection(
                SubSection(
                    ModbusInterface,
                    name="modbus",
                    description="Interact with a running Modbus Interface container",
                )
            )

        self.args = args = parser.parse_args()

        # remove grcp logging while using cli
        os.environ["GRPC_VERBOSITY"] = "ERROR"
        os.environ["GRPC_TRACE"] = ""
        logging.getLogger().setLevel(logging.ERROR)
        sys.stdout.reconfigure(line_buffering=True)

        try:
            passed_args = {
                k: v
                for k, v in vars(args).items()
                if k in inspect.signature(args.callback).parameters.keys()
            }
            if "kwargs" in inspect.signature(args.callback).parameters.keys():
                passed_args = {k: v for k, v in vars(args).items()}
            args.callback(**passed_args)
        except Exception as e:
            if args.debug:
                traceback.print_exc()
            else:
                print(f"An error occurred: {e}")

    def add_grpc_subsection(self, subsection: SubSection):
        subsection.mount_sub_section(self.subparser)
        self.added_subsections.append(subsection)

    def main(self):
        pass
