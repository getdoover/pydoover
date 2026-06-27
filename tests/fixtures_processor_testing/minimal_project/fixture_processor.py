from __future__ import annotations

from pydoover.processor import Application


class FixtureProcessor(Application):
    async def on_manual_invoke(self, event):
        print("manual invoke handled")
        await self.api.update_channel_aggregate(
            "status",
            {"state": event.payload["state"]},
            log_update=True,
            replace_keys=["state"],
        )
