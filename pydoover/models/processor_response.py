from typing import Any


class ProcessorTokenResponse:
    """Response from put_schedule and create_ingestion_endpoint."""

    def __init__(self, id: int, token: str, token_id: int):
        self.id = int(id)
        self.token = token
        self.token_id = int(token_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            id=int(data["id"]),
            token=data["token"],
            token_id=int(data["token_id"]),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "token_id": self.token_id,
        }
