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
    from .abc import User
    from .attachment import Attachment
    from .cache._types import CacheProtocol
    from .channels import PartialChannel
    from .member import PartialMember
    from .message import PartialMessage
    from .role import Role

# mostly to prevent circular imports and such things

__all__ = ("ResolvedData",)


class ResolvedData:
    """The resolved user, member, role, channel, message, and attachment data for an
    object.
    """

    def __init__(self, data: dict[str, Any] | None, cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache

        self._users: dict[int, User] = {}
        self._roles: dict[int, Role] = {}
        self._channels: dict[int, PartialChannel] = {}
        self._messages: dict[int, PartialMessage] = {}
        self._attachments: dict[int, Attachment] = {}

        self._update(data)

    def _update(self, data: dict[str, Any] | None) -> None:
        if not data:
            return

        cache = self._cache
        members = data.get("members", {})
        guild_id = self
