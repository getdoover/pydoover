class Object:
    """Represents a generic doover object.

    This allows you to create a "basic" object that can be passed into
    functions that expect an object, but only use the `.id` attribute.
    """

    def __init__(self, id: str):
        self.id = id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    def to_dict(self):
        """Convert the object to a dictionary representation."""
        return {"id": self.id}
