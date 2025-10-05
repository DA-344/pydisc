"""
pydisc.cache
~~~~~~~~~~~~

Sub-module that implements caching logic for a Client.
"""

from ._types import CacheProtocol
from .default import DefaultCache

__all__ = (
    "CacheProtocol",
    "DefaultCache",
)
