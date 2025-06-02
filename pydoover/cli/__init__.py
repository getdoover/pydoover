import logging

from .cli import CLI


def entrypoint():
    """
    Entry point for the Doover CLI.
    """
    logging.basicConfig(level=logging.INFO)
    CLI().main()
