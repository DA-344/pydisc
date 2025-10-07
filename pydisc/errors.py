"""
The MIT License (MIT)

Copyright (c) 2025-present Developer Anonymous

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse
    from requests import Response

    _Response = ClientResponse | Response

__all__ = (
    "PydiscException",
    "HTTPException",
    "Forbidden",
    "NotFound",
    "DiscordServerError",
    "GatewayConnectionClosed",
    "GatewayReconnectNeeded",
    "WebSocketClosure",
)


class PydiscException(Exception):
    """Base class for all exceptions in the library."""


def _flatten_error_dict(d: dict[str, Any], key: str = "") -> dict[str, str]:
    items: list[tuple[str, str]] = []
    for k, v in d.items():
        new_key = f"{key}.{k}" if key else k

        if isinstance(v, dict):
            v: dict[Any, Any]
            try:
                _errors: list[dict[str, Any]] = v["_errors"]
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, " ".join(x.get("message", "") for x in _errors)))
        else:
            items.append((new_key, v))
    return dict(items)


class HTTPException(PydiscException):
    """Base class for all exceptions related to HTTP requests in the library."""

    def __init__(self, response: _Response, message: dict[str, Any] | str | None) -> None:
        self.response: _Response = response
        """The response that failed."""
        self.status: int = response.status  # type: ignore # filled even when using requests
        """The failure status code."""
        self.code: int
        """The status code in which the request failed."""
        self.text: str
        """The text of the error. This could be empty."""

        if isinstance(message, dict):
            self.code = message.get("code", 0)
            base = message.get("message", "")
            errors = message.get("errors")
            self._errors: dict[str, Any] | None = errors
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = "\n".join("In %s: %s" % t for t in errors.items())
                self.text = base + "\n" + helpful
            else:
                self.text = base
        else:
            self.text = message or ""
            self.code = 0

        fmt = "{0.status} {0.reason} (error code: {1})"
        if len(self.text):
            fmt += ": {2}"

        super().__init__(fmt.format(self.response, self.code, self.text))


class Forbidden(HTTPException):
    """An exception raised when a 403 ocurrs."""


class NotFound(HTTPException):
    """An exception raised when a 404 ocurrs."""


class DiscordServerError(HTTPException):
    """An exception raised when a status code at range of [500, 600) ocurrs."""


class RateLimited(PydiscException):
    """An error raised when a 429 is received by Discord."""

    def __init__(self, retry_after: float) -> None:
        self.retry_after: float = retry_after
        """The amount of time to wait in order to retry the request."""
        super().__init__(f"Too many requests. Retry in {retry_after:.2f} seconds.")


class GatewayConnectionClosed(PydiscException):
    """Exception raised when a gateway connection is closed."""

    def __init__(self, ws: ClientWebSocketResponse, *, code: int | None = None) -> None:
        self.code: int = code or ws.close_code or -1
        """The code with which the gateway was closed with."""
        super().__init__(f"WebSocket closed with code {self.code}")


class GatewayReconnectNeeded(PydiscException):
    """Exception raised when a gateway asks for a reconnection."""

    def __init__(self, *, resume: bool = True) -> None:
        self.resume: bool = resume
        self.op: str = "IDENTIFY" if resume is False else "RESUME"
        super().__init__("Gateway sent a RECONNECT opcode, you should reconnect")


class WebSocketClosure(PydiscException):
    """Exception raised when a websocket connection closes."""


class PriviligedIntentsRequired(PydiscException):
    """Excpetion raised when the gateway requests intents the app has not applied for.

    For non-verified bots, this can be solved by ticking the checkbox in the intents
    you need at https://discord.com/developers/applications/

    For verified bots, you should apply to enable the intent. Until then, you can not use it.

    The currently available priviliged intents are:

    - :attr:`Intents.members`
    - :attr:`Intents.message_content`
    - :attr:`Intents.presences`
    """

    def __init__(self) -> None:
        super().__init__(
            "Your application is requesting priviliged intents that have not been explicitly enabled in the "
            "developer portal. You should go to https://discord.com/developers/applications/ "
            "and tick all those intents you need and have enabled in your code. If this can not be done, you should "
            "remove the conflicting Intent from the intents flags."
        )


class ImproperToken(PydiscException):
    """Excpetion raised when you pass a non-valid token to login into Discord."""
