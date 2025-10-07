"""
pydisc.websockets
~~~~~~~~~~~~~~~~~

Sub-module that handles everything websocket-related in the library.
"""

from .decompressor import ActiveDecompressor, Decompressor
from .enums import GatewayCloseCodes, GatewayOPCodes
from .poller import DiscordWebSocketPoller
from .response import DiscordWebSocketResponse

__all__ = (
    "DiscordWebSocketPoller",
    "ActiveDecompressor",
    "Decompressor",
    "GatewayOPCodes",
    "GatewayCloseCodes",
    "DiscordWebSocketResponse",
)
