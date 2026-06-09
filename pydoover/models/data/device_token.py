class RotatedDeviceToken:
    """Response from ``POST /agents/{agent_id}/token/rotate``.

    The newly-minted v1 mini-token. The caller must persist it, switch its
    authentication to use it, then call ``confirm_device_token`` *with this
    token as the bearer* to retire the previous one. Until that confirm step
    succeeds, the previous token remains valid — so a device that loses this
    response in transit can keep using the old token and retry.
    """

    def __init__(self, token: str, issued_at_ms: int):
        self.token = token
        self.issued_at_ms = issued_at_ms

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["token"], data["issued_at_ms"])


class ConfirmedDeviceToken:
    """Response from ``POST /agents/{agent_id}/token/confirm``.

    ``tokens_valid_from`` is the new revocation floor (unix-ms). Every v1
    mini-token for this agent issued before this timestamp is now rejected.
    """

    def __init__(self, tokens_valid_from: int):
        self.tokens_valid_from = tokens_valid_from

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["tokens_valid_from"])
