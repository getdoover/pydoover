try:
    from .generated.device_agent.device_agent_pb2 import (
        TurnCredential as ProtoTurnCredential,
    )

    _HAS_PROTO = True
except ImportError:
    _HAS_PROTO = False


class TurnCredential:
    # pub struct TurnTokenResponse {
    #     username: String,
    #     credential: String,
    #     ttl: u64,
    #     expires_at: u64,
    #     uris: Vec<String>,
    # }
    def __init__(
        self,
        username: str,
        credential: str,
        ttl: int,
        expires_at: int,
        uris: list[str],
    ):
        self.username = username
        self.credential = credential
        self.ttl = ttl
        self.expires_at = expires_at
        self.uris = uris

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data["username"],
            data["credential"],
            data["ttl"],
            data["expires_at"],
            data["uris"],
        )

    @classmethod
    def from_proto(cls, resp):
        return cls(
            resp.username,
            resp.credential,
            resp.ttl,
            resp.expires_at,
            list(resp.uris),
        )

    def to_proto(self):
        if not _HAS_PROTO:
            raise RuntimeError("Proto stubs not available")
        return ProtoTurnCredential(
            username=self.username,
            credential=self.credential,
            ttl=self.ttl,
            expires_at=self.expires_at,
            uris=self.uris,
        )
