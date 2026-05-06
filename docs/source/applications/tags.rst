.. py:currentmodule:: pydoover.tags

Tags
====

Tags are named values an application publishes to the Doover cloud. The
runtime maintains two views of every tag:

* an **aggregate** — the current value, refreshed continuously and used
  by dashboards and other consumers; and
* a **log** — a stream of timestamped channel messages used for graphs
  and historical analysis.

By default, docker applications batch tag updates into the aggregate
once per main-loop iteration and emit one log message at most every 15
minutes. Cloud processors flush at the end of each invocation. Both
behaviours can be overridden per call via ``log=True`` (see below).

Declaring tags
--------------

Tags are declared as class attributes on a :class:`Tags` subclass. Use
the typed subclasses — :class:`Number`, :class:`Boolean`,
:class:`String` — when you want IDE autocomplete to surface
type-specific options like threshold-based logging::

    from pydoover.tags import Tags, Number, Boolean, String

    class MyTags(Tags):
        voltage = Number(default=0.0, log_on_cross=[90, 110], deadband=2)
        fault   = Boolean(default=False, log_on_change=True)
        state   = String(log_on_state=["error", "ok"])

The legacy form ``Tag("number", default=0)`` still works and is fully
supported.

Inside an application the runtime exposes a :class:`BoundTag` proxy::

    await self.tags.voltage.set(102)
    current = self.tags.voltage.get()
    await self.tags.fault.delete()


Logging an update immediately
-----------------------------

Pass ``log=True`` to :meth:`BoundTag.set` (or :meth:`~BoundTag.increment`
/ :meth:`~BoundTag.decrement`) to mark the update for an immediate
logged data point — published as a channel message at the end of the
current main-loop iteration in docker apps, or at the end of the
current invocation in processors::

    await self.tags.voltage.set(120, log=True)

Multiple ``log=True`` calls within the same loop coalesce into one
channel message. The same path is also reused by the trigger system
described below, so anything fired automatically follows the same flush
cadence.

Deleting a tag
--------------

Use :meth:`BoundTag.delete` to remove a tag from the aggregate channel.
This is the documented way to express deletion intent — prefer it over
``tag.set(None)``::

    await self.tags.voltage.delete()
    await self.tags.voltage.delete(log=True)  # also record the deletion

Threshold-driven auto-logging
-----------------------------

The typed tag classes accept declarative trigger configuration. When a
trigger fires, the update is automatically promoted to ``log=True``.

Numeric crossings
~~~~~~~~~~~~~~~~~

:class:`Number` accepts ``log_on_cross`` (a scalar or list of
thresholds) and an optional ``deadband``. A crossing fires when the
value moves from one side of a threshold to the other; the implicit
prior side is ``below``, so an initial value above any threshold also
logs::

    voltage = Number(log_on_cross=[90, 110], deadband=2)

With ``deadband=2``, the crossing only fires once the value clears
``threshold ± deadband / 2``. This suppresses repeat logs while the
value oscillates close to the threshold.

State transitions
~~~~~~~~~~~~~~~~~

:class:`Boolean` and :class:`String` accept four trigger options:

* ``log_on_change=True`` — log every transition.
* ``log_on_state=[...]`` — log when entering OR exiting any of the
  listed values.
* ``log_on_enter=[...]`` — log only when entering one of the listed
  values.
* ``log_on_exit=[...]`` — log only when exiting one of the listed
  values.

``log_on_state`` is sugar for passing the same list to both
``log_on_enter`` and ``log_on_exit``; the three can be combined.

API reference
-------------

.. autoclass:: pydoover.tags.Tag
   :members:
   :show-inheritance:

.. autoclass:: pydoover.tags.Number
   :members:
   :show-inheritance:

.. autoclass:: pydoover.tags.Boolean
   :members:
   :show-inheritance:

.. autoclass:: pydoover.tags.String
   :members:
   :show-inheritance:

.. autoclass:: pydoover.tags.RemoteTag
   :members:
   :show-inheritance:

.. autoclass:: pydoover.tags.Tags
   :members:

.. autoclass:: pydoover.tags.BoundTag
   :members:
