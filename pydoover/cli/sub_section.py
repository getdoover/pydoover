import argparse
import asyncio
import inspect
import typing
from typing import Any, Protocol, cast

from .parsers import (
    extract_description,
    extract_parameters,
    json_or_str,
    int_or_list,
    bool_or_list,
    float_or_list,
    comma_separated_list,
    BoolFlag,
)


class SubSection:
    def __init__(
        self,
        section_class,
        name: str = "subcommands",
        description: str | None = None,
    ):
        self.name = name
        self.description = description
        self.section_class = section_class

        self.uri_remapping = None
        self.section_params = []
        self.init_signature = None

        self.setup_base_arguments()

        self.subparser = None

    def mount_sub_section(self, arg_parser):
        sub_section_parser = arg_parser.add_parser(
            name=self.name, help=self.description
        )
        sub_section_parser.set_defaults(callback=sub_section_parser.print_help)

        for param_name, kwargs in self.section_params:
            sub_section_parser.add_argument(param_name, **kwargs)

        self.subparser = sub_section_parser.add_subparsers(title="Subcommands")

        for name, func in inspect.getmembers(
            self.section_class, predicate=inspect.isfunction
        ):
            func = cast(_CommandFunction, func)
            if not getattr(func, "_is_command", False):
                continue

            parser = self.subparser.add_parser(
                func._command_name,
                description=extract_description(func._command_help),
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )

            # Callback to call the function on the correct class passing the correct aguments to both the interface class and the method
            def func_caller(func_to_run=func, **kwargs):
                if "uri" in kwargs:
                    if self.uri_remapping is None:
                        raise Exception("uri not remapped but has been supplied")
                    kwargs[self.uri_remapping] = kwargs["uri"]

                kwargs["app_key"] = "pydoover-cli"
                # Create the interface class
                object_instance = self.section_class(
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if self.init_signature is not None
                        and k in self.init_signature.parameters.keys()
                    }
                )

                # Run the method on the interface class
                try:
                    func_kwargs = {
                        k: v
                        for k, v in kwargs.items()
                        if k in inspect.signature(func_to_run).parameters.keys()
                    }
                    result = func_to_run(object_instance, **func_kwargs)
                    if inspect.iscoroutine(result):
                        result = asyncio.run(result)
                except Exception as e:
                    print(
                        f"An error occurred while running {func_to_run.__name__}: {e}"
                    )
                    return

                if result is not None:
                    if hasattr(result, "to_dict"):
                        result = result.to_dict()
                    print(result)

            parser.set_defaults(callback=func_caller)
            argspec = inspect.signature(func)
            doc_string_paramaters = extract_parameters(func._command_help)
            arg_docs = func._command_arg_docs

            for param in argspec.parameters.values():
                kwargs: dict[str, Any] = {"help": arg_docs.get(param.name)}
                if param.name == "self":
                    continue
                if param.name in doc_string_paramaters:
                    kwargs["help"] = (
                        doc_string_paramaters[param.name][0]
                        + " - "
                        + doc_string_paramaters[param.name][1]
                    )
                param_name = param.name

                if param.default is not inspect.Parameter.empty:
                    kwargs["default"] = param.default
                    kwargs["required"] = False
                    param_name = "--" + param_name

                self.parse_arg_type(param, kwargs)

                try:
                    parser.add_argument(param_name, **kwargs)
                except ValueError:
                    print(
                        f"Failed to setup command {self.name}.{name} parameter type: {str(param.annotation)} is unknown, please add a handler"
                    )

            if func._command_setup_api:
                parser.add_argument(
                    "--profile", help="Config profile to use.", default="default"
                )
                parser.add_argument(
                    "--agent",
                    help="Agent query string (name or ID) to use for this request.",
                    type=str,
                    default="default",
                )

            parser.add_argument(
                "--enable-traceback",
                help=argparse.SUPPRESS,
                default=False,
                action="store_true",
            )

    def setup_base_arguments(self):
        # find all the parameters needed for the base interface
        for name, func in inspect.getmembers(
            self.section_class, predicate=inspect.isfunction
        ):
            if name != "__init__":
                continue

            self.init_signature = inspect.signature(func)
            # doc_string_paramaters = parsers.extract_parameters(func._command_help)
            arg_docs = {}
            if hasattr(func, "_command_arg_docs"):
                arg_docs = func._command_arg_docs

            for param in self.init_signature.parameters.values():
                kwargs: dict[str, Any] = {"help": arg_docs.get(param.name)}
                if param.name == "self":
                    continue
                # if param.name in doc_string_paramaters:
                #     kwargs["help"] = doc_string_paramaters[param.name][0] + " - " + doc_string_paramaters[param.name][1]
                param_name = param.name

                if "uri" in param_name:
                    self.uri_remapping = param_name
                    param_name = "uri"
                elif "app_key" in param_name:
                    continue

                if param.default is not inspect.Parameter.empty:
                    kwargs["default"] = param.default
                    kwargs["required"] = False
                    param_name = "--" + param_name
                else:
                    print(
                        f"Error, grcp class ({self.section_class.__name__}) has a non default __init__ paramater: {param_name}"
                    )
                    continue

                self.parse_arg_type(param, kwargs)

                self.section_params.append((param_name, kwargs))

    def parse_arg_type(self, param, kwargs):
        annotation = param.annotation

        if annotation is BoolFlag:
            kwargs["action"] = (
                "store_false" if kwargs["default"] is True else "store_true"
            )
        elif annotation == typing.Union[int, list[int]]:
            kwargs["type"] = int_or_list
        elif annotation == typing.Union[bool, list[bool]]:
            kwargs["type"] = bool_or_list
        elif annotation == typing.Union[float, list[float]]:
            kwargs["type"] = float_or_list
        elif annotation == typing.Union[dict, str]:
            kwargs["type"] = json_or_str
        elif annotation is not inspect.Parameter.empty:
            # Handle union types (e.g. int | None, list[str] | None)
            cli_type = self._resolve_cli_type(annotation)
            if cli_type is not None:
                kwargs["type"] = cli_type
            else:
                kwargs["type"] = annotation
        return kwargs

    @staticmethod
    def _resolve_cli_type(annotation):
        """Extract a CLI-friendly type from a union annotation.

        For unions like ``int | None`` or ``int | datetime | None``, returns
        the first concrete scalar type suitable for argparse.  For
        ``list[str] | None`` returns a comma-separated-list parser.

        Returns ``None`` when the annotation is not a union or cannot be
        simplified.
        """
        # Normalise both typing.Union and PEP 604 (int | None) forms
        args = typing.get_args(annotation)
        if not args:
            return None

        # Filter out NoneType
        non_none = [a for a in args if a is not type(None)]
        if not non_none:
            return None

        # list[str] | None  ->  comma_separated_list
        if len(non_none) == 1:
            origin = typing.get_origin(non_none[0])
            if origin is list:
                inner = typing.get_args(non_none[0])
                if inner and inner[0] is str:
                    return comma_separated_list

        # Pick the best scalar type from the remaining args
        # Prefer int > float > str, skip datetime (CLI will pass ints)
        for preferred in (int, float, str):
            if preferred in non_none:
                return preferred

        return None
    
    
class _CommandFunction(Protocol):
    __name__: str
    _is_command: bool
    _command_name: str
    _command_help: str
    _command_arg_docs: dict[str, str]
    _command_setup_api: bool

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
