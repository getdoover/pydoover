class Object:
    """Represents a generic doover object.

    This allows you to create a "basic" object that can be passed into
    functions that expect an object, but only use the `.key` attribute.
    """

    def __init__(self, key: str):
        self.key = key

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.key == other.key
        return NotImplemented

    def to_dict(self):
        """Convert the object to a dictionary representation."""
        return {"key": self.key}
