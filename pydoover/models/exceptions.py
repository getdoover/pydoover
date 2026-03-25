class DooverAPIError(Exception):
    """Base exception for Doover API errors."""


class HTTPError(DooverAPIError):
    """HTTP error with status code and response body."""

    def __init__(self, status: int, message: str, url: str = ""):
        self.status = status
        self.url = url
        super().__init__(f"HTTP {status} on {url}: {message}")


class NotFoundError(HTTPError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Not found", url: str = ""):
        super().__init__(404, message, url)


class ForbiddenError(HTTPError):
    """Access denied (403)."""

    def __init__(self, message: str = "Forbidden", url: str = ""):
        super().__init__(403, message, url)


class BadRequestError(HTTPError):
    """Bad request (400)."""

    def __init__(self, message: str = "Bad request", url: str = ""):
        super().__init__(400, message, url)


class UnauthorizedError(HTTPError):
    """Authentication failed (401)."""

    def __init__(self, message: str = "Unauthorized", url: str = ""):
        super().__init__(401, message, url)


class TokenRefreshError(DooverAPIError):
    """Failed to refresh the access token."""
