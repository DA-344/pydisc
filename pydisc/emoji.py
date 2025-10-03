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

import asyncio
import re
from typing import TYPE_CHECKING, Any

from .mixins import Hashable
from .utils import _get_snowflake

if TYPE_CHECKING:
    from .user import User
    from .cache._types import CacheProtocol

CUSTOM_EMOJI_PATTERN = re.compile(r"<?(?:(?P<animated>a)?:)?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?")

__all__ = (
    "Emoji",
)


class Emoji(Hashable):
    """Represents a Discord emoji.

    Emojis can be constructed either via initializing this
    and providing an ``id``, ``name``, and an optionally ``animated``
    flag, or by using ``Emoji.from_str`` and letting the library parse the emoji name for you.
    """

    def __init__(
        self,
        name: str,
        *,
        id: int | None = None,
        animated: bool = False,
    ) -> None:
        self.id: int | None = id
        """The ID of this emoji."""
        self.name: str = name
        """The name of this emoji."""
        self.animated: bool = animated
        """Whether this emoji is animated."""
        self.user: User | None = None
        """The user that created this emoji."""
        self._role_ids: list[int] | None = None
        self.require_colons: bool = False
        """Whether this emoji requires to be wrapped in colons."""
        self.managed: bool = False
        """Whether this emoji is managed."""
        self.available: bool = True
        """Whether this emoji is available for usage."""

        self._updated: asyncio.Event = asyncio.Event()

    def is_partial(self) -> bool:
        """Returns whether this emoji is partial or not. An emoji is considered partial
        when it has not been received from the API or has not been updated with API data.
        """
        return self._updated.is_set()

    def is_unicode(self) -> bool:
        """Whether this emoji is unicode or not."""
        return self.id is None

    def is_custom(self) -> bool:
        """Whether this emoji is custom or not."""
        return self.id is not None

    def __str__(self) -> str:
        if self.is_unicode():
            return self.name
        string = "<{animated}{name}:{id}>"
        return string.format(
            animated="a:" if self.animated else "",
            name=self.name,
            id=self.id,
        )

    def _update(self, payload: dict[str, Any], cache: CacheProtocol) -> None:
        self.id = _get_snowflake("id", payload) or self.id
        self.name = payload["name"]
        self.animated = payload.get("animated", self.animated)
        self._role_ids = list(map(int, payload.get("roles", [])))
        self.require_colons = payload.get("require_colons", False)
        self.managed = payload.get("managed", False)
        self.available = payload.get("available", True)

        if user := payload.get("user"):
            if self.user is not None:
                self.user.__init__(user, cache)
            else:
                self.user = cache.get_user(int(user["id"])) or cache._create_user(user)

        self._updated.set()

    @classmethod
    def from_str(cls, emoji: str, /) -> Emoji:
        """Creates a new :class:`Emoji` instance from a string, which can either be
        a unicode or custom emoji.

        The currently supported formats are:

        - ``a:name:id``
        - ``<a:name:id>``
        - ``name:id``
        - ``<name:id>``

        Or unicode if none of the previous patterns match.
        """

        match = CUSTOM_EMOJI_PATTERN.match(emoji)

        if match is not None:
            groups = match.groupdict()

            animated = bool(groups["animated"])
            id = int(groups["id"])
            name = groups["name"]
            return Emoji(name, id=id, animated=animated)
        return Emoji(emoji)

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
        }

        if self.animated:
            pd["animated"] = self.animated

        return pd

    @classmethod
    def from_dict(cls, data: dict[str, Any], state: CacheProtocol) -> Emoji:
        self = Emoji(name=data["name"])
        self._update(data, state)
        return self
