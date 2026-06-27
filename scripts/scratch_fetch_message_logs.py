#!/usr/bin/env python3
"""Fetch processor invocation logs for a known message.

Run with:
    uv run python scripts/scratch_fetch_message_logs.py --profile staging
"""

from __future__ import annotations

import argparse
import json
import os

from pydoover.api import DataClient


BASE_URL = "https://data.doover.com/api"
AGENT_ID = 190979190017803266
CHANNEL_NAME = "dv-proc-inv-190979385044550663"
MESSAGE_ID = 193588160649819432


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        default=os.environ.get("PYDOOVER_PROFILE", "default"),
        help="Auth profile to use. Defaults to PYDOOVER_PROFILE or 'default'.",
    )
    parser.add_argument(
        "--organisation-id",
        type=int,
        default=os.environ.get("PYDOOVER_ORG_ID"),
        help="Optional X-Doover-Organisation id.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with DataClient(
        base_url=BASE_URL,
        profile=args.profile,
        organisation_id=args.organisation_id,
    ) as client:
        entries = client.fetch_message_logs(
            AGENT_ID,
            CHANNEL_NAME,
            MESSAGE_ID,
        )

    print(json.dumps([entry.to_dict() for entry in entries], indent=2))


if __name__ == "__main__":
    main()
