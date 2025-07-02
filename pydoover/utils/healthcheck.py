"""Simple script to check the health of the running application.

This is exposed as the `doover-app-healthcheck` command.
"""

import os
from subprocess import run


def main():
    port = os.environ.get("HEALTHCHECK_PORT", 49200)
    try:
        run(["curl", f"http://127.0.0.1:{port}/health"], check=True)
    except Exception:
        success = False
    else:
        success = True

    if success:
        print("OK")
        exit(0)
    else:
        print("FAIL")
        exit(1)
