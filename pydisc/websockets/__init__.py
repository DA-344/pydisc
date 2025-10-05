"""
pydisc.websockets
~~~~~~~~~~~~~~~~~

Sub-module that handles everything websocket-related in the library.
"""

from .poller import DiscordWebSocketPoller
from .decompressor import ActiveDecompressor, Decompressor
from .enums import GatewayOPCodes, GatewayCloseCodes
from .response import DiscordWebSocketResponse

__all__ = (
    "DiscordWebSocketPoller",
    "ActiveDecompressor",
    "Decompressor",
    "GatewayOPCodes",
    "GatewayCloseCodes",
    "DiscordWebSocketResponse",
)
