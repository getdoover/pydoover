"""Simple script to check the health of the running application.

This is exposed as the `doover-app-healthcheck` command.
"""

from contextlib import suppress

import requests


def main():
    success = False
    with suppress(Exception):
        response = requests.get("http://127.0.0.1:49200/healthcheck")
        if response.status_code == 200:
            success = True

    if success:
        print("OK")
        exit(0)
    else:
        print("FAIL")
        exit(1)
