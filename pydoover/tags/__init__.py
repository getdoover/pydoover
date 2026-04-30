from typing import Any, Iterator, NoReturn, overload

from .manager import TagsManager
from ..config import Schema


class NotSet:
    """Sentinel used when a tag has not been assigned a value."""


def _coerce_tag_value(value: Any, tag_type: str) -> Any:
    """Coerce a tag value to match its declared type.

    JSON does not distinguish between integers and floats, so values
    from channels often arrive as float even when the tag is declared
    as ``"integer"``.  This function normalises the value based on the
    declared ``tag_type``.
    """
    if value is None or value is NotSet:
        return value
    if tag_type == "integer" and isinstance(value, float) and value.is_integer():
        return int(value)
    if tag_type == "boolean" and not isinstance(value, bool):
        return bool(value)
    return value


class Tag:
    """Represents a single declared tag definition."""

    def __init__(self, tag_type: str, default: Any = NotSet, name: str | None = None):
        self.tag_type = tag_type
        self.name = name
        self.default = default
        self._declared_attr_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert this tag definition to its schema-style dictionary form."""
        data = {"type": self.tag_type}
        if self.default is not NotSet:
            data["default"] = self.default
        return data

    def to_schema(self) -> dict[str, Any]:
        """Alias for :meth:`to_dict` to match the rest of the declarative API."""
        return self.to_dict()

    def __repr__(self) -> str:
        return f"Tag(name={self.name!r}, tag_type={self.tag_type!r}, default={self.default!r})"

    def _raise_unbound_error(self) -> NoReturn:
        raise RuntimeError(
            "Declared Tag definitions are not runtime values. "
            "Access tags through a Tags instance."
        )

    @property
    def value(self) -> Any:
        self._raise_unbound_error()

    def get(self) -> Any:
        self._raise_unbound_error()

    def set(self, value: Any) -> Any:
        del value
        self._raise_unbound_error()

    def clear(self) -> Any:
        self._raise_unbound_error()

    def is_set(self) -> bool:
        self._raise_unbound_error()

    def increment(self, amount: int | float = 1) -> Any:
        del amount
        self._raise_unbound_error()

    def decrement(self, amount: int | float = 1) -> Any:
        del amount
        self._raise_unbound_error()

    def __str__(self) -> str:
        self._raise_unbound_error()

    def __bool__(self) -> bool:
        self._raise_unbound_error()

    def __int__(self) -> int:
        self._raise_unbound_error()

    def __float__(self) -> float:
        self._raise_unbound_error()

    def __lt__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __le__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __gt__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def __ge__(self, other: Any) -> bool:
        del other
        self._raise_unbound_error()

    def _resolve_target(
        self, tags: "Tags", declaration: "_DeclaredTag"
    ) -> tuple[str | None, str]:
        """Return ``(app_key, key_name)`` for manager-backed get/set calls.

        The default implementation routes through the owning ``Tags`` instance's
        own ``app_key`` and the declared tag name. Subclasses (e.g.
        :class:`RemoteTag`) override this to redirect reads and writes
        elsewhere.
        """
        return tags.app_key, declaration.name


class _UnresolvedRemoteTag(Exception):
    """Internal: an optional :class:`RemoteTag` has no resolved upstream target.

    Raised by :meth:`RemoteTag._resolve_target` when the matching
    :class:`pydoover.config.TagRef` was left blank by the operator. Caught
    by :meth:`Tags._get_tag_value` (returns the declared default) and
    :meth:`Tags._set_tag_value` (silently no-ops).
    """


class RemoteTag(Tag):
    """A tag declaration that resolves to a tag published by another application.

    The runtime target is described by a :class:`pydoover.config.TagRef` config
    element whose ``reference_name`` matches this tag's ``reference_name``. The
    binding happens at setup time via :meth:`Tags._resolve_remote_tags`.

    When ``republish_locally`` is true (the default), the resolved upstream
    value is mirrored into this app's own tag namespace under the
    ``reference_name`` key — so other consumers on the device (UIs,
    downstream tags) can read it as if it were a local tag.

    Cross-agent references (``agent_id`` set on the underlying
    :class:`~pydoover.config.TagRef`) are accepted in the schema but raise
    :class:`NotImplementedError` at runtime: the wiring is deferred so the
    schema does not need to change later.

    Parameters
    ----------
    tag_type:
        Asserted by the developer (matches the upstream type).
    reference_name:
        Local handle; must match a ``TagRef`` config element's
        ``reference_name``.
    republish_locally:
        Mirror upstream changes into this app's namespace under
        ``reference_name``. Defaults to ``True``. No-op on managers that do
        not support subscriptions (e.g. processor contexts).
    default:
        Returned when the manager has no value for the upstream tag.
    name:
        Optional explicit declaration name (otherwise inherits the attribute
        name on the owning :class:`Tags` subclass).
    """

    def __init__(
        self,
        tag_type: str,
        *,
        reference_name: str,
        republish_locally: bool = True,
        default: Any = NotSet,
        name: str | None = None,
        optional: bool = False,
    ):
        # Optional RemoteTags need a sensible read-fallback when the matching
        # TagRef is left blank. Default to None so callers don't have to
        # restate it on every declaration.
        if optional and default is NotSet:
            default = None

        super().__init__(tag_type, default=default, name=name)
        self.reference_name = reference_name
        self.republish_locally = republish_locally
        self.optional = optional

    def __repr__(self) -> str:
        return (
            f"RemoteTag(name={self.name!r}, reference_name={self.reference_name!r}, "
            f"tag_type={self.tag_type!r}, republish_locally={self.republish_locally}, "
            f"optional={self.optional})"
        )

    def _resolve_target(
        self, tags: "Tags", declaration: "_DeclaredTag"
    ) -> tuple[str | None, str]:
        # Resolution state lives on the Tags instance because templates are
        # shared across all instances of a given Tags subclass.
        try:
            target = tags._remote_tag_targets[declaration.attr_name]
        except KeyError as exc:
            if self.optional:
                # Operator left the matching TagRef blank — caller falls
                # back to the declared default (read) or no-ops (write).
                raise _UnresolvedRemoteTag from exc
            raise RuntimeError(
                f"RemoteTag '{declaration.attr_name}' has not been resolved "
                f"against the config. The application framework should call "
                f"`await tags._resolve_remote_tags()` after `Tags.setup()`."
            ) from exc

        if target["agent_id"]:
            raise NotImplementedError(
                f"Cross-agent RemoteTag (agent_id={target['agent_id']!r}) "
                "is not yet supported."
            )
        return target["app_key"], target["tag_name"]


class BoundTag:
    """Manager-backed runtime view of a declared tag.

    A ``BoundTag`` is what you interact with on a :class:`Tags` instance.
    Reads and writes are delegated to the registered tag manager.
    """

    _NUMERIC_TAG_TYPES = {"number", "integer", "float"}

    def __init__(self, tags: "Tags", declaration: "_DeclaredTag"):
        self._tags = tags
        self._declaration = declaration

    @property
    def _is_async(self) -> bool:
        return self._tags._is_async

    @property
    def name(self) -> str:
        """str: The resolved runtime name of this tag."""
        return self._declaration.name

    @property
    def tag_type(self) -> str:
        """str: The declared tag type."""
        return self._declaration.template.tag_type

    @property
    def default(self) -> Any:
        """Any: The default value returned when no runtime value exists."""
        return self._declaration.template.default

    @property
    def value(self) -> Any:
        """Any: Convenience alias for :meth:`get`."""
        return self.get()

    def get(self) -> Any:
        """Return the current value of this tag from the registered manager."""
        return self._tags._get_tag_value(self._declaration.attr_name)

    async def set(self, value: Any) -> None:
        """Async variant of :meth:`set`."""
        await self._tags._set_tag_value(self._declaration.attr_name, value)

    async def clear(self) -> None:
        """Reset this tag back to its declared default value."""
        await self.set(self.default)

    def is_set(self) -> bool:
        """Return ``True`` when this tag currently has a concrete value."""
        return self.get() is not NotSet

    async def increment(self, amount: int | float = 1) -> Any:
        """Increment a numeric tag and return the new value."""
        self._validate_numeric("increment")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot increment unset tag '{self.name}'.")
        new_value = current + amount
        await self.set(new_value)
        return new_value

    async def decrement(self, amount: int | float = 1) -> Any:
        """Decrement a numeric tag and return the new value."""
        self._validate_numeric("decrement")
        current = self.get()
        if current is NotSet:
            raise ValueError(f"Cannot decrement unset tag '{self.name}'.")
        new_value = current - amount
        await self.set(new_value)
        return new_value

    def _validate_numeric(self, operation: str) -> None:
        if self.tag_type not in self._NUMERIC_TAG_TYPES:
            raise TypeError(
                f"Cannot {operation} non-numeric tag '{self.name}' of type '{self.tag_type}'."
            )

    def _compare(self, other: Any, comparator):
        return comparator(self.get(), other)

    def __repr__(self) -> str:
        return f"BoundTag(name={self.name!r}, value={self.get()!r})"

    def __copy__(self):
        return self

    def __deepcopy__(self, _memo):
        return self

    def __str__(self) -> str:
        return str(self.get())

    def __bool__(self) -> bool:
        return bool(self.get())

    def __int__(self) -> int:
        return int(self.get())

    def __float__(self) -> float:
        return float(self.get())

    def __eq__(self, other: Any) -> bool:
        return self.get() == other

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a < b)

    def __le__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a <= b)

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a > b)

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, lambda a, b: a >= b)


class _DeclaredTag:
    def __init__(self, attr_name: str, template: Tag):
        self.attr_name = attr_name
        self.template = template

    @property
    def name(self) -> str:
        return self.template.name or self.attr_name

    @overload
    def __get__(self, instance: None, owner: type["Tags"]) -> Tag: ...

    @overload
    def __get__(self, instance: "Tags", owner: type["Tags"]) -> BoundTag: ...

    def __get__(self, instance: "Tags | None", owner: type["Tags"]) -> Tag | BoundTag:
        if instance is None:
            return self.template
        return BoundTag(instance, self)

    def __set__(self, instance: "Tags", value: Any) -> None:
        if isinstance(value, BoundTag):
            return
        instance._set_tag_value(self.attr_name, value)


class Tags:
    """Base class for declarative tag definitions.

    Subclasses declare available tags as class attributes. Instances expose
    manager-backed :class:`BoundTag` proxies and may also mutate their available
    tag set at runtime via :meth:`add_tag` and :meth:`remove_tag`.
    """

    __tag_declarations__: "dict[str, _DeclaredTag]" = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        declarations: "dict[str, _DeclaredTag]" = dict()
        for base in reversed(cls.__mro__[1:]):
            declarations.update(getattr(base, "__tag_declarations__", {}))

        for attr_name, value in list(cls.__dict__.items()):
            if not isinstance(value, Tag):
                continue

            value._declared_attr_name = attr_name
            declaration = _DeclaredTag(attr_name, value)
            declarations[attr_name] = declaration
            setattr(cls, attr_name, declaration)

        cls.__tag_declarations__ = declarations

    def __init__(self, app_key: str, tag_manager: TagsManager, config: Schema):
        self.config = config
        self._manager = tag_manager
        self.app_key = app_key

        # Keep runtime declaration changes isolated to this instance.
        self._tag_declarations = dict(self.__class__.__tag_declarations__)

        # Resolved targets for declared RemoteTags, keyed by attr_name.
        # Populated by `_resolve_remote_tags()`.
        self._remote_tag_targets: dict[str, dict[str, Any]] = {}

    async def setup(self):
        """Mutate this tag collection before it is bound to a manager."""
        pass

    async def _resolve_remote_tags(self):
        """Bind every declared :class:`RemoteTag` to its config-side ``TagRef``.

        Walks ``self.config`` collecting every ``TagRef`` element by
        ``reference_name``, then matches each declared :class:`RemoteTag` to
        exactly one entry. Raises :class:`ValueError` on missing or duplicate
        matches, and on duplicate ``reference_name`` values across the config.

        For RemoteTags with ``republish_locally=True``, registers a
        manager-level subscription that mirrors upstream changes into this
        app's own namespace under ``reference_name`` and seeds the local
        mirror with the current upstream value (if any).

        Cross-agent ``TagRef`` entries (where ``agent_id`` is set) are
        recorded but not subscribed to — see :meth:`RemoteTag._resolve_target`
        for the runtime behaviour.

        Only top-level ``TagRef`` elements on the schema are scanned for v1.
        """
        from ..config import TagRef  # local import to avoid module-load cycles
        from ..config import (
            NotSet as ConfigNotSet,
        )  # distinct sentinel from tags.NotSet

        refs_by_name: dict[str, TagRef] = {}
        if self.config is not None:
            for elem in getattr(self.config, "_element_map", {}).values():
                if not isinstance(elem, TagRef):
                    continue
                # An optional TagRef left blank has reference_name unset —
                # skip it so optional RemoteTags fall through to their
                # declared default at read time. (Note: `ConfigNotSet` is
                # the config-module sentinel, distinct from `tags.NotSet`.)
                if elem.reference_name._value is ConfigNotSet:
                    continue
                ref_name = elem.reference_name.value
                if ref_name in refs_by_name:
                    raise ValueError(
                        f"Duplicate TagRef reference_name {ref_name!r} in config."
                    )
                refs_by_name[ref_name] = elem

        # Always re-resolve from scratch — keeps the operation idempotent and
        # avoids stale state when a Tags instance is reused.
        self._remote_tag_targets = {}

        for declaration in self._tag_declarations.values():
            template = declaration.template
            if not isinstance(template, RemoteTag):
                continue

            try:
                tagref = refs_by_name[template.reference_name]
            except KeyError as exc:
                if template.optional:
                    # Optional RemoteTag with no filled-in TagRef — silently
                    # skip; reads return the declared default.
                    continue
                raise ValueError(
                    f"RemoteTag {declaration.attr_name!r} references "
                    f"reference_name={template.reference_name!r}, but no "
                    f"TagRef with that reference_name was found in the config."
                ) from exc

            agent_id = tagref.agent_id.value or None
            target = {
                "agent_id": agent_id,
                "app_key": tagref.app_name.value,
                "tag_name": tagref.tag_name.value,
            }
            self._remote_tag_targets[declaration.attr_name] = target

            if (
                template.republish_locally
                and self._manager is not None
                and not agent_id
            ):
                await self._install_remote_mirror(template, target)

    async def _install_remote_mirror(
        self, template: "RemoteTag", target: dict[str, Any]
    ) -> None:
        """Register the republish-locally subscription for a resolved RemoteTag.

        No-op on managers that do not support tag subscriptions (e.g.
        processor contexts).
        """
        subscribe = getattr(self._manager, "subscribe_to_tag", None)
        if subscribe is None:
            return

        ref_name = template.reference_name
        local_app_key = self.app_key
        upstream_app_key = target["app_key"]
        upstream_tag_name = target["tag_name"]
        manager = self._manager

        async def _mirror(_key, value):
            await manager.set_tag(ref_name, value, app_key=local_app_key)

        subscribe(upstream_tag_name, _mirror, app_key=upstream_app_key)

        # Seed the local mirror with the current upstream value so other
        # consumers see something on first read instead of waiting for the
        # next upstream change.
        current = manager.get_tag(
            upstream_tag_name, default=NotSet, app_key=upstream_app_key
        )
        if current is not NotSet and current is not None:
            await manager.set_tag(ref_name, current, app_key=local_app_key)

    @property
    def definitions(self) -> list[Tag]:
        """list[Tag]: The declared tag definitions for this instance."""
        return [declaration.template for declaration in self._tag_declarations.values()]

    @property
    def values(self) -> dict[str, Any]:
        """dict[str, Any]: The current manager-backed values for all declared tags."""
        return {
            declaration.name: self._get_tag_value(attr_name)
            for attr_name, declaration in self._tag_declarations.items()
            if self._get_tag_value(attr_name) is not NotSet
        }

    def _get_declaration(self, name: str) -> _DeclaredTag | None:
        for attr_name, declaration in self._tag_declarations.items():
            if attr_name == name or declaration.name == name:
                return declaration
        return None

    def add_tag(self, name: str, tag: Tag) -> Tag:
        """Add a tag definition to this instance.

        This is primarily intended for config-dependent tag factories, where the
        available tag set needs to be customized before user code runs.
        """
        if not isinstance(tag, Tag):
            raise TypeError("add_tag expects a Tag instance.")
        if self._get_declaration(name) is not None:
            raise ValueError(f"Tag '{name}' already exists.")

        declaration = _DeclaredTag(name, tag)
        if self._get_declaration(declaration.name) is not None:
            raise ValueError(f"Tag '{declaration.name}' already exists.")

        self._tag_declarations[name] = declaration
        return declaration.template

    def remove_tag(self, name: str) -> None:
        """Remove a tag definition from this instance."""
        declaration = self._get_declaration(name)
        if declaration is None:
            raise KeyError(name)
        del self._tag_declarations[declaration.attr_name]

    def _get_tag_value(self, name: str) -> Any:
        declaration = self._get_declaration(name)
        if declaration is None:
            raise AttributeError(f"Unknown tag '{name}'")

        if self._manager is None:
            return declaration.template.default

        try:
            app_key, key_name = declaration.template._resolve_target(self, declaration)
        except _UnresolvedRemoteTag:
            return declaration.template.default

        value = self._manager.get_tag(
            key_name,
            default=declaration.template.default,
            app_key=app_key,
        )
        return _coerce_tag_value(value, declaration.template.tag_type)

    async def _set_tag_value(self, name: str, value: Any) -> None:
        declaration = self._get_declaration(name)
        if declaration is None:
            raise AttributeError(f"Unknown tag '{name}'")
        if self._manager is None:
            raise RuntimeError("Tags manager has not been registered.")

        try:
            app_key, key_name = declaration.template._resolve_target(self, declaration)
        except _UnresolvedRemoteTag:
            # Optional RemoteTag with no upstream — silently no-op so apps
            # don't need to branch on resolution state at every write site.
            return

        await self._manager.set_tag(key_name, value, app_key=app_key)

    def get(self, name: str) -> BoundTag | None:
        """Return the bound runtime proxy for a tag, if it exists."""
        return self.find_tag(name)

    def find_tag(self, name: str) -> BoundTag | None:
        """Return the bound runtime proxy for a tag, if it exists."""
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return BoundTag(self, declaration)

    def get_tag(self, name: str) -> BoundTag:
        """Return the bound runtime proxy for a tag.

        Raises
        ------
        KeyError
            If the tag does not exist on this collection.
        """
        tag = self.find_tag(name)
        if tag is None:
            raise KeyError(name)
        return tag

    def get_definition(self, name: str) -> Tag | None:
        """Return the declared :class:`Tag` definition for a tag, if it exists."""
        declaration = self._get_declaration(name)
        if declaration is None:
            return None
        return declaration.template

    async def update(self, values: dict[str, Any]) -> None:
        """Update multiple tag values through their bound runtime proxies."""
        for key, value in values.items():
            tag = self.find_tag(key)
            if tag is not None:
                await tag.set(value)

    def to_dict(self) -> dict[str, Any]:
        """Return the current manager-backed tag values."""
        return self.values

    def to_schema(self) -> dict[str, Any]:
        """Return the schema-style definitions for the current tag set."""
        return {
            declaration.name: declaration.template.to_schema()
            for declaration in self._tag_declarations.values()
        }

    def __iter__(self) -> Iterator[BoundTag]:
        for name in self._tag_declarations:
            tag = self.find_tag(name)
            if tag is not None:
                yield tag

    def __len__(self):
        return len(self._tag_declarations)

    def __getitem__(self, item: str) -> BoundTag:
        return self.get_tag(item)

    def __getattr__(self, name: str) -> BoundTag:
        tag = self.find_tag(name)
        if tag is None:
            raise AttributeError(name)
        return tag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._tag_declarations)})"
