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

from typing import TYPE_CHECKING, Any, Literal

from pydisc.abc import Messageable
from pydisc.enums import ChannelType, try_enum

from .core import GuildChannel

if TYPE_CHECKING:
    from pydisc.cache._types import CacheProtocol


class TextChannel(GuildChannel, Messageable):
    """Represents a :class:`pydisc.Guild` text :class:`pydisc.abc.Channel`.

    This inherits from :class:`pydisc.GuildChannel`.
    """

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)

        self._type: ChannelType = try_enum(ChannelType, data["type"])

    @property
    def type(self) -> Literal[ChannelType.text, ChannelType.announcement]:
        return self._type  # pyright: ignore[reportReturnType]

    def is_news(self) -> bool:
        """Whether this channel is a news channel."""
        return self.type is ChannelType.announcement
