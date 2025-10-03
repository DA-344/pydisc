"""
pydisc.events
~~~~~~~~~~~~~

Sub-module that manages the event receiving and invoking of the library.
"""

from . import models
from .router import EventRouter

__all__ = (
    "EventRouter",
    "models",
)
