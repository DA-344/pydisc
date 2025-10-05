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

from .color import Color
from .emoji import Emoji

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .message import Message

__all__ = ("Reaction",)


class Reaction:
    """Represents a message reaction."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, message: Message) -> None:
        self.count: int = data["count"]
        """The total number of times this emoji has been reacted to. Includes burst reactions."""
        self.count_details: ReactionCountDetails = ReactionCountDetails(data["count_details"])
        """The details of the total count of reactions."""
        self.reacted: bool = data["me"]
        """Whether the current user has added this reaction to the message."""
        self.burst_reacted: bool = data["me_burst"]
        """Whether the current user has added this super reaction to the message."""
        self.emoji: Emoji = Emoji.from_dict(data["emoji"], cache)
        """A partial Emoji this reaction is from."""
        self.burst_colors: list[Color] = [Color.from_str(c) for c in data.get("burst_colors", [])]
        """The colors used for the burst reactions."""
        self.message: Message = message
        """The message this reaction is from."""

    @property
    def normal_count(self) -> int:
        """A shortcut for :attr:`Reaction.count_details.normal <ReactionCountDetails.normal>`."""
        return self.count_details.normal

    @property
    def burst_count(self) -> int:
        """A shortcut for :attr:`Reaction.count_details.burst <ReactionCountDetails.burst>`."""
        return self.count_details.burst

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None, cache: CacheProtocol, message: Message) -> list[Reaction]:
        if not data:
            return []
        return [Reaction(r, cache, message) for r in data]


class ReactionCountDetails:
    """Represents the count details of a reaction."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.burst: int = data["burst"]
        """The count of super reactions."""
        self.normal: int = data["normal"]
        """The count of normal reactions."""
