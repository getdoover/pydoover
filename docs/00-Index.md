# PyDoover Documentation

Welcome to the PyDoover developer documentation vault. This Obsidian vault contains comprehensive documentation for the `pydoover` Python package (v0.4.18) for developing applications on the Doover IoT/Industrial automation platform.

## Quick Links

- [Doover Website](https://doover.com)
- [General Documentation](https://docs.doover.com)
- [PyDoover API Reference](https://pydoover.readthedocs.io)

## Getting Started

- [[01-Getting-Started|Getting Started Guide]]
- [[02-Quick-Reference|Quick Reference Card]]
- [[03-Project-Structure|Project Structure Overview]]

## Core Modules

### Device Applications
- [[10-Application-Framework|Application Framework]] - Building device applications
- [[11-Application-Lifecycle|Application Lifecycle]] - Setup, main loop, and shutdown
- [[12-Tags-and-Channels|Tags and Channels]] - Inter-app communication

### Configuration
- [[20-Configuration-System|Configuration System]] - Define app configuration schemas
- [[21-Config-Types|Configuration Types]] - Integer, String, Boolean, Enum, etc.
- [[22-Config-Schema-Export|Schema Export]] - Generating JSON Schema for UI

### User Interface
- [[30-UI-System-Overview|UI System Overview]] - Building user interfaces
- [[31-UI-Variables|Variables]] - Read-only display elements
- [[32-UI-Interactions|Interactions]] - Actions, sliders, commands
- [[33-UI-Containers|Containers and Submodules]] - Organizing UI elements
- [[34-UI-Decorators|UI Decorators]] - @action, @slider, @callback patterns

### Cloud Integration
- [[40-Cloud-API|Cloud API Client]] - REST API interactions
- [[41-Cloud-Processors|Cloud Processors]] - Server-side message processing
- [[42-Channels-and-Messages|Channels and Messages]] - Cloud messaging

### Hardware Interfaces
- [[50-gRPC-Interfaces|gRPC Interfaces Overview]]
- [[51-Device-Agent-Interface|Device Agent Interface]] - Cloud sync
- [[52-Platform-Interface|Platform Interface]] - Digital/Analog I/O
- [[53-Modbus-Interface|Modbus Interface]] - Modbus RTU/TCP

### Utilities
- [[60-Utilities|Utilities Overview]]
- [[61-State-Machine|State Machine]] - Managing application state
- [[62-Reports|Reports]] - Excel report generation

## Examples & Tutorials

- [[70-Tutorial-Basic-App|Tutorial: Creating a Basic Application]]
- [[71-Tutorial-UI-Elements|Tutorial: Building UI Elements]]
- [[72-Tutorial-Modbus|Tutorial: Modbus Communication]]
- [[73-Example-Patterns|Common Patterns and Best Practices]]

## Reference

- [[80-API-Quick-Reference|API Quick Reference]]
- [[81-Common-Errors|Common Errors and Solutions]]
- [[82-Changelog|Version History]]

---

## Installation

```bash
# Using uv (recommended)
uv add pydoover

# Using pip
pip install -U pydoover

# With gRPC support
pip install -U pydoover[grpc]

# Development install
uv sync --all-extras --all-groups
```

## Python Version

**Python 3.11 or higher is required**

---

## Tags

#pydoover #doover #iot #documentation #index
