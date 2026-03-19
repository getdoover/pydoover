from typing import Any


class SubscriptionInfo:
    def __init__(
        self,
        agent_id: int,
        organisation_id: int,
        app_key: str,
        deployment_config: dict[str, Any],
        ui_state: dict[str, Any],
        ui_cmds: dict[str, Any],
        tag_values: dict[str, Any],
        connection_data: dict[str, Any],
        token: str,
    ):
        self.agent_id = agent_id
        self.organisation_id = organisation_id
        self.app_key = app_key
        self.deployment_config = deployment_config
        self.ui_state = ui_state
        self.ui_cmds = ui_cmds
        self.tag_values = tag_values
        self.connection_data = connection_data
        self.token = token

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["agent_id"]),
            organisation_id=int(data["organisation_id"]),
            app_key=data["app_key"],
            deployment_config=data["deployment_config"],
            ui_state=data["ui_state"],
            ui_cmds=data["ui_cmds"],
            tag_values=data["tag_values"],
            connection_data=data["connection_data"],
            token=data["token"],
        )

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "organisation_id": self.organisation_id,
            "app_key": self.app_key,
            "deployment_config": self.deployment_config,
            "ui_state": self.ui_state,
            "ui_cmds": self.ui_cmds,
            "tag_values": self.tag_values,
            "connection_data": self.connection_data,
            "token": self.token,
        }
