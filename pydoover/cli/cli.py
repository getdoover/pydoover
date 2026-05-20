import argparse
import inspect
import shlex
import traceback

import logging
import os
import sys
from typing import Any, cast

from .sub_section import SubSection


# Printed on its own stdout line after every command handled in --shell mode
# (non-interactive only). A command's result can span multiple lines — error
# messages in particular (e.g. multi-line gRPC tracebacks) — or zero lines
# (commands returning None, or unknown subcommands that argparse rejects). The
# sentinel lets a machine client delimit one command's output from the next
# regardless of how many lines it produced.
SHELL_COMMAND_SENTINEL = "__PYDOOVER_SHELL_CMD_END__"


_GRPC_SUBSECTIONS = {
    "platform": (
        "..docker.platform",
        "PlatformInterface",
        "Interact with a running Platform Interface container",
    ),
    "device_agent": (
        "..docker.device_agent",
        "DeviceAgentInterface",
        "Interact with a running Device Agent container",
    ),
    "modbus": (
        "..docker.modbus",
        "ModbusInterface",
        "Interact with a running Modbus Interface container",
    ),
}


def _detect_requested_subcommand(argv):
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        return arg if arg in _GRPC_SUBSECTIONS else None
    return None


class CLI:
    def __init__(self):
        self._shell_mode = "--shell" in sys.argv

        self.parser = argparse.ArgumentParser(
            prog="pydoover", description="Interact with running gRPC servers."
        )
        self.parser.set_defaults(callback=self.parser.print_help)
        self.parser.add_argument(
            "--shell",
            action="store_true",
            help="Read commands from stdin one per line in a single long-lived "
            "process. Avoids Python/import startup cost on every call.",
        )

        self.subparser = self.parser.add_subparsers(
            dest="subcommand", title="Subcommands"
        )
        self.added_subsections = []

        if self._shell_mode:
            sections_to_load = list(_GRPC_SUBSECTIONS)
        else:
            requested = _detect_requested_subcommand(sys.argv)
            sections_to_load = (
                [requested] if requested is not None else list(_GRPC_SUBSECTIONS)
            )

        self._load_subsections(sections_to_load)

        # remove grcp logging while using cli
        os.environ["GRPC_VERBOSITY"] = "ERROR"
        os.environ["GRPC_TRACE"] = ""
        logging.getLogger().setLevel(logging.ERROR)
        stdout = cast(Any, sys.stdout)
        if hasattr(stdout, "reconfigure"):
            stdout.reconfigure(line_buffering=True)

        if self._shell_mode:
            self._run_shell()
        else:
            self.args = args = self.parser.parse_args()
            self._dispatch(args)

    def _load_subsections(self, sections_to_load):
        from importlib import import_module

        try:
            for section_name in sections_to_load:
                module_path, class_name, description = _GRPC_SUBSECTIONS[section_name]
                module = import_module(module_path, package=__package__)
                interface_class = getattr(module, class_name)
                self.add_grpc_subsection(
                    SubSection(
                        interface_class,
                        name=section_name,
                        description=description,
                    )
                )
        except ImportError as e:
            print(e)
            print(
                "Docker interfaces not found. GRPC CLI support will not be available."
            )

    def _dispatch(self, args):
        try:
            sig_params = inspect.signature(args.callback).parameters
            if "kwargs" in sig_params:
                passed_args = dict(vars(args))
            else:
                passed_args = {k: v for k, v in vars(args).items() if k in sig_params}
            args.callback(**passed_args)
        except Exception as e:
            if getattr(args, "enable_traceback", False) or getattr(
                args, "debug", False
            ):
                traceback.print_exc()
            else:
                print(f"An error occurred: {e}")

    def _run_shell(self):
        is_tty = sys.stdin.isatty()
        if is_tty:
            print(
                "pydoover shell — type a subcommand (e.g. 'platform fetch_ai 0'), "
                "'exit' or Ctrl+D to quit.",
                file=sys.stderr,
            )

        while True:
            try:
                line = input("pydoover> " if is_tty else "")
            except EOFError:
                if is_tty:
                    print(file=sys.stderr)
                return
            except KeyboardInterrupt:
                if is_tty:
                    print(file=sys.stderr)
                    continue
                return

            line = line.strip()
            if line in ("exit", "quit"):
                return

            # Process the line; the `finally` always emits the end-of-command
            # sentinel (machine mode only) so a client can delimit this
            # command's output from the next, even when it printed zero lines
            # (None result / unknown subcommand) or many (multi-line error).
            try:
                if not line or line.startswith("#"):
                    continue

                try:
                    args_list = shlex.split(line)
                except ValueError as e:
                    print(f"Parse error: {e}", file=sys.stderr)
                    continue

                try:
                    args = self.parser.parse_args(args_list)
                except SystemExit:
                    # argparse exits on --help or arg errors; stay in the shell.
                    continue

                try:
                    self._dispatch(args)
                except KeyboardInterrupt:
                    print("Interrupted.", file=sys.stderr)
            finally:
                if not is_tty:
                    print(SHELL_COMMAND_SENTINEL)
                sys.stdout.flush()
                sys.stderr.flush()

    def add_grpc_subsection(self, subsection: SubSection):
        subsection.mount_sub_section(self.subparser)
        self.added_subsections.append(subsection)

    def main(self):
        pass
