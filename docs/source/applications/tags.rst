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

Tags are declared as class attributes on a :class:`Tags` subclass.
Use the typed classes — :class:`Number`, :class:`Boolean`,
:class:`String` — for every declaration::

    from pydoover.tags import Tags, Number, Boolean, String, Cross, AnyChange, Enter, Exit

    class MyTags(Tags):
        voltage = Number(default=0.0, log_on=Cross(90, 110, deadband=2))
        fault   = Boolean(default=False, log_on=AnyChange())
        state   = String(log_on=[Enter("error"), Exit("error")])

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

The typed tag classes take a single ``log_on=`` parameter that accepts
one descriptor or a list of descriptors. When any descriptor fires, the
update is automatically promoted to ``log=True``.

Numeric tags
~~~~~~~~~~~~

:class:`Number` accepts :class:`Cross`, :class:`Rise`, :class:`Fall`,
and :class:`Delta`. Crossing descriptors take one or more thresholds as
positional arguments plus an optional ``deadband`` keyword::

    voltage = Number(log_on=Cross(100, deadband=2))   # both directions
    multi   = Number(log_on=Cross(90, 100, 110))      # multiple thresholds
    pressure = Number(log_on=Rise(110))               # high alarm
    fuel     = Number(log_on=Fall(10))                # low alarm
    pump     = Number(log_on=[Rise(110), Fall(10)])   # high + low

A crossing fires when the value moves from one side of a threshold to
the other. The implicit prior side is "below", so an initial value
above any threshold also logs (whereas an initial value below it does
not).

``deadband`` widens each threshold into a hysteresis band: a crossing
only fires once the value moves at least ``deadband / 2`` past the
threshold, suppressing repeat logs while the value oscillates close to
it. The "silent" opposite direction still updates the internal state
machine, so subsequent crossings the other way work correctly.

:class:`Delta` logs whenever the value moves far enough from the *last
value this descriptor logged on* — useful for analog signals that
drift continuously rather than crossing fixed thresholds. Specify
exactly one of ``amount=`` (absolute change) or ``percent=`` (relative
change against the last logged value)::

    flow    = Number(log_on=Delta(amount=5))    # log on ±5 unit moves
    rpm     = Number(log_on=Delta(percent=10))  # log on ±10% swings

The first set always fires so graphs have a baseline data point.
Combine descriptors freely — e.g. ``log_on=[Cross(100), Delta(amount=5)]``
captures both alarm transitions and significant drift.

Boolean and string tags
~~~~~~~~~~~~~~~~~~~~~~~

:class:`Boolean` and :class:`String` accept :class:`AnyChange`,
:class:`Enter`, and :class:`Exit`. :class:`Enter` and :class:`Exit`
each take a single value — combine them in a list to react to multiple
values or both directions::

    fault   = Boolean(log_on=AnyChange())             # every transition
    state   = String(log_on=Enter("error"))           # only entering "error"
    state   = String(log_on=Exit("ok"))               # only exiting "ok"

    # Bidirectional on a single value:
    state   = String(log_on=[Enter("error"), Exit("error")])

    # Multiple "interesting" values, both directions:
    state   = String(log_on=[
        Enter("error"), Exit("error"),
        Enter("ok"),    Exit("ok"),
    ])

    # Asymmetric: log entry to "error" but exit from "ok":
    state   = String(log_on=[Enter("error"), Exit("ok")])

Type validation
~~~~~~~~~~~~~~~

Each typed tag accepts only its corresponding descriptors —
``Number(log_on=AnyChange())`` raises :class:`TypeError` at class
definition time, surfacing the mistake before the application runs.

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

Trigger descriptors
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pydoover.tags.Cross
.. autoclass:: pydoover.tags.Rise
.. autoclass:: pydoover.tags.Fall
.. autoclass:: pydoover.tags.Delta
.. autoclass:: pydoover.tags.AnyChange
.. autoclass:: pydoover.tags.Enter
.. autoclass:: pydoover.tags.Exit

.. autoclass:: pydoover.tags.Tags
   :members:

.. autoclass:: pydoover.tags.BoundTag
   :members:
