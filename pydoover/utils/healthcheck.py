"""Simple script to check the health of the running application.

This is exposed as the `doover-app-healthcheck` command.
"""

import os
from contextlib import suppress

import requests


def main():
    success = False
    port = os.environ.get("HEALTHCHECK_PORT", 49200)
    with suppress(Exception):
        response = requests.get(f"http://127.0.0.1:{port}/healthcheck")
        if response.status_code == 200:
            success = True

    if success:
        print("OK")
        exit(0)
    else:
        print("FAIL")
        exit(1)
