class DooverException(Exception):
    """General exception class for Doover API errors"""


class HTTPException(DooverException):
    """Error class for HTTP-related issues"""


class NotFound(DooverException):
    """Error raised when a resource is not found"""


class Forbidden(DooverException):
    """Error raised when access to a resource is forbidden"""
