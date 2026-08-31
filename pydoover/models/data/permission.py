from typing import Any


class ResourcePermission:
    """A single permission grant: a resource ID plus its permission bit string."""

    def __init__(self, permission_id: str, permission: str):
        self.permission_id = permission_id
        self.permission = permission

    def __repr__(self):
        return (
            f"ResourcePermission(permission_id={self.permission_id!r}, "
            f"permission={self.permission!r})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            permission_id=data["permission_id"],
            permission=data["permission"],
        )

    def to_dict(self):
        return {
            "permission_id": self.permission_id,
            "permission": self.permission,
        }


class AgentPermission:
    """The full resolved permission set for an agent."""

    def __init__(
        self,
        agent_id: int,
        is_superuser: bool,
        resources: list[ResourcePermission],
        last_updated: int | None = None,
    ):
        self.agent_id = agent_id
        self.is_superuser = is_superuser
        self.resources = resources
        self.last_updated = last_updated

    def __repr__(self):
        return (
            f"AgentPermission(agent_id={self.agent_id!r}, "
            f"is_superuser={self.is_superuser!r}, "
            f"resources={len(self.resources)})"
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            agent_id=int(data["agent_id"]),
            is_superuser=data["is_superuser"],
            resources=[
                ResourcePermission.from_dict(r) for r in data.get("resources", [])
            ],
            last_updated=data.get("last_updated"),
        )

    def to_dict(self):
        result = {
            "agent_id": self.agent_id,
            "is_superuser": self.is_superuser,
            "resources": [r.to_dict() for r in self.resources],
        }
        if self.last_updated is not None:
            result["last_updated"] = self.last_updated
        return result
