.. py:currentmodule:: pydoover

Client
======

.. autoclass:: pydoover.ui.UIManager
    :members:

Declarative UI
==============

``ui.UI`` is the preferred way to declare application UI structure.
It mirrors the declarative ``Tags`` API: define elements as class attributes,
declare the UI and tags classes on your application via ``ui_cls`` and
``tags_cls``, and keep dynamic values tag-backed where appropriate.
By default, tag-backed fields serialize to the compact frontend lookup format
such as ``$tag.voltage:number`` rather than the expanded object form.

.. autoclass:: pydoover.ui.UI
    :members:

Static declarative UI example::

    from pydoover import ui
    from pydoover.tags import Number, Tags

    class MyTags(Tags):
        voltage = Number()

    class MyUI(ui.UI):
        voltage = ui.NumericVariable(
            "voltage",
            "Voltage",
            curr_val=MyTags.voltage,
        )

Explicit tag helper example::

    from pydoover import ui

    class MyUI(ui.UI):
        voltage = ui.NumericVariable(
            "voltage",
            "Voltage",
            curr_val=ui.tag_ref("voltage", tag_type="number"),
        )

Application wiring example::

    from pydoover.docker import Application
    from pydoover.config import Schema

    class MyApp(Application):
        config_cls = Schema
        tags_cls = MyTags
        ui_cls = MyUI

Config-aware setup example::

    from pydoover import ui
    from pydoover.tags import Number, String, Tags

    class ConfiguredTags(Tags):
        voltage = Number()

        async def setup(self, config):
            if config.show_extra.value:
                self.add_tag("extra", String())

    class ConfiguredUI(ui.UI):
        voltage = ui.NumericVariable(
            "voltage",
            "Voltage",
            curr_val=ConfiguredTags.voltage,
        )

        async def setup(self, config, tags):
            if config.show_extra.value:
                self.add_element("extra", ui.TextVariable("extra", "Extra"))

Legacy note:
Existing instance-based UI construction through ``UIManager.add_children()``,
``set_ui()``, and decorator-generated elements remains supported.

Elements
========

Elements are the building blocks of the Doover UI. They represent various components that can be used to create user interfaces for applications.

:class:`Element` is the base class that all other elements inherit from. Following are some miscellaneous elements that are commonly used in applications.

.. autoclass:: pydoover.ui.Element
    :members:

.. autoclass:: pydoover.ui.ConnectionInfo
    :members:

.. autoclass:: pydoover.ui.AlertStream
    :members:

.. autoclass:: pydoover.ui.Multiplot
    :members:

``Multiplot`` now prefers the Doover 2.0 record-based ``series`` schema. Legacy
list-based series definitions remain supported as deprecated input and are normalized
to the newer payload shape on serialization.

.. autoclass:: pydoover.ui.RemoteComponent


Interactions
============

Interactions are a form of UI element that allows users to interact with the application.
They can be used to trigger actions, change state, or provide input.
Use ``Button`` and ``Select`` for new code. ``Action``, ``SlimCommand``, and
``StateCommand`` remain as compatibility aliases for older Doover 1.0 UI payloads.

.. autoclass:: pydoover.ui.Interaction
    :members:

.. autoclass:: pydoover.ui.Button
    :members:

.. autoclass:: pydoover.ui.Select
    :members:

.. autoclass:: pydoover.ui.Action
    :members:

.. autoclass:: pydoover.ui.WarningIndicator
    :members:

.. autoclass:: pydoover.ui.HiddenValue
    :members:

.. autoclass:: pydoover.ui.SlimCommand
    :members:

.. autoclass:: pydoover.ui.StateCommand
    :members:

.. autoclass:: pydoover.ui.Slider
    :members:


Variables
=========

Variables are read-only elements that can be used to display information in the UI,
and are expected to be updated through the lifecycle of an application. Some common examples include the solar voltage, pump state or humidity reading.

.. autoclass:: pydoover.ui.Variable
    :members:

.. autoclass:: pydoover.ui.NumericVariable
    :members:

.. autoclass:: pydoover.ui.TextVariable
    :members:

.. autoclass:: pydoover.ui.BooleanVariable
    :members:

.. autoclass:: pydoover.ui.DateTimeVariable
    :members:


Parameters
==========

Parameters are input fields with various validations for different types. They expect a callback that is executed when a user modifies the input.
Use ``FloatInput``, ``TextInput``, ``DatetimeInput``, and ``TimeInput`` for new code.
The ``*Parameter`` classes remain available as deprecated compatibility aliases.

.. autoclass:: pydoover.ui.Parameter
    :members:

.. autoclass:: pydoover.ui.FloatInput
    :members:

.. autoclass:: pydoover.ui.TextInput
    :members:

.. autoclass:: pydoover.ui.DatetimeInput
    :members:

.. autoclass:: pydoover.ui.TimeInput
    :members:

.. autoclass:: pydoover.ui.NumericParameter
    :members:

.. autoclass:: pydoover.ui.TextParameter
    :members:

.. autoclass:: pydoover.ui.BooleanParameter
    :members:

.. autoclass:: pydoover.ui.DateTimeParameter
    :members:


Decorators
----------

Decorators can be used as a shortcut to add UI interactions with an associated callback function.

.. autofunction:: pydoover.ui.callback

.. autofunction:: pydoover.ui.button

.. autofunction:: pydoover.ui.select

.. autofunction:: pydoover.ui.action

.. autofunction:: pydoover.ui.warning_indicator

.. autofunction:: pydoover.ui.hidden_value

.. autofunction:: pydoover.ui.state_command

.. autofunction:: pydoover.ui.slider

.. autofunction:: pydoover.ui.float_input

.. autofunction:: pydoover.ui.text_input

.. autofunction:: pydoover.ui.datetime_input

.. autofunction:: pydoover.ui.time_input

.. autofunction:: pydoover.ui.numeric_parameter

.. autofunction:: pydoover.ui.text_parameter

.. autofunction:: pydoover.ui.boolean_parameter

.. autofunction:: pydoover.ui.datetime_parameter


Submodules
==========

.. autoclass:: pydoover.ui.Container
    :members:

.. autoclass:: pydoover.ui.Submodule
    :members:
    :inherited-members:

.. autoclass:: pydoover.ui.Application
    :members:


Miscellaneous
=============

.. autoclass:: pydoover.ui.Colour
    :members:

.. autoclass:: pydoover.ui.Range
    :members:

.. autoclass:: pydoover.ui.Option
    :members:

.. autoclass:: pydoover.ui.Widget
    :members:
