.. py:currentmodule:: pydoover

Client
======

.. autoclass:: pydoover.ui.UIManager
    :members:

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

.. autoclass:: pydoover.ui.RemoteComponent


Interactions
============

Interactions are a form of UI element that allows users to interact with the application.
They can be used to trigger actions, change state, or provide input.

.. autoclass:: pydoover.ui.Interaction
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

.. autoclass:: pydoover.ui.Parameter
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

.. autofunction:: pydoover.ui.action

.. autofunction:: pydoover.ui.warning_indicator

.. autofunction:: pydoover.ui.hidden_value

.. autofunction:: pydoover.ui.state_command

.. autofunction:: pydoover.ui.slider

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
