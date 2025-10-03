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

from .core import _RichGetterModel

__all__ = (
    "ChannelCreate",
    "ChannelUpdate",
    "ChannelDelete",
)

if TYPE_CHECKING:
    from pydisc.cache._types import CacheProtocol
    from pydisc.abc import Channel

    class _ChannelEvent(_RichGetterModel, Channel):
        data: Channel
else:
    class _ChannelEvent(_RichGetterModel):
        def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
            from pydisc.channels.factory import channel_factory
            self.data: Channel = channel_factory(data, cache)


ChannelCreate = _ChannelEvent
"""Represents an ``on_channel_create`` event payload."""
ChannelUpdate = _ChannelEvent
"""Represents an ``on_channel_update`` event payload."""
ChannelDelete = _ChannelEvent
"""Represents an ``on_channel_delete`` event payload."""
