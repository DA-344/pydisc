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

from typing import TYPE_CHECKING, Any, Self

import aiohttp

from pydisc.utils import Protocol

if TYPE_CHECKING:
    from pydisc import abc
    from pydisc.channels import Thread
    from pydisc.client import Client
    from pydisc.commands import Command, ContextMenu, Group
    from pydisc.components import Component
    from pydisc.emoji import Emoji
    from pydisc.guild import Guild
    from pydisc.http import RESTHandler
    from pydisc.member import Member
    from pydisc.message import Message
    from pydisc.soundboard import SoundboardSound
    from pydisc.sticker import Sticker
    from pydisc.user import User

__all__ = ("CacheProtocol",)


# TODO: maybe allow for this to be async? idk
class CacheProtocol(Protocol):
    """Represents a cache protocol allowed to be passed to a client.

    You may subclass this in order to implement your own custom cache.

    You can find an implementation at :class:`DefaultCache`.

    All methods must be overridden in order for this cache to work.

    Methods Guide
    -------------
    ``get_`` methods:
        They all take an ``id`` as ``int | None`` and return the respective object or ``None``.
        You should handle the cases in which the ``id`` is ``None``.
    ``store_`` methods:
        They all take the object to be stored, and should not return anything.
    ``remove_`` methods:
        They all take the ``id`` of the object type to remove. You should return the deleted object, or
        ``None`` if it was not present.
    """

    def __init__(self, client: Client[Self]) -> None:
        self.client: Client[Self] = client
        self.http: RESTHandler = client.http
        self.session: aiohttp.ClientSession = self.http.session

    def get_guild(self, id: int | None, /) -> Guild | None:
        """Gets a guild from the cache."""
        raise NotImplementedError

    def store_guild(self, guild: Guild, /) -> None:
        """Stores a guild in the cache."""
        raise NotImplementedError

    def remove_guild(self, id: int, /) -> Guild | None:
        """Removes a guild from the cache."""
        raise NotImplementedError

    def get_user(self, id: int | None, /) -> User | None:
        """Gets a user from the cache."""
        raise NotImplementedError

    def store_user(self, user: User, /) -> None:
        """Stores a user in the cache."""
        raise NotImplementedError

    def remove_user(self, id: int, /) -> User | None:
        """Removes a user from the cache."""
        raise NotImplementedError

    def get_custom_emoji(self, id: int | None, /) -> Emoji | None:
        """Gets a custom emoji from the cache."""
        raise NotImplementedError

    def store_custom_emoji(self, emoji: Emoji, /) -> None:
        """Stores a custom emoji in the cache."""
        raise NotImplementedError

    def remove_custom_emoji(self, id: int, /) -> Emoji | None:
        """Removes a custom emoji from the cache."""
        raise NotImplementedError

    def _create_user(self, data: dict[str, Any]) -> User:
        from pydisc.user import User

        obj = User(data, self)
        self.store_user(obj)
        return obj

    def _create_message(self, data: dict[str, Any]) -> Message:
        from pydisc.message import Message

        ret = Message(data, self)
        if self.get_message(ret.id) is None:
            self.store_message(ret)
        return ret

    def get_command(self, name: str | None, /) -> Command | Group | ContextMenu | None:
        """Gets a command from the cache."""
        raise NotImplementedError

    def store_command(self, command: Command | Group | ContextMenu, /) -> None:
        """Stores a command in the cache."""
        raise NotImplementedError

    def remove_command(self, name: str, /) -> Command | Group | ContextMenu | None:
        """Removes a command from the cache."""

    def get_channel(self, id: int | None, /) -> abc.Channel | None:
        """Gets a channel from the cache."""
        raise NotImplementedError

    def store_channel(self, channel: abc.Channel, /) -> None:
        """Stores a channel in the cache."""
        raise NotImplementedError

    def remove_channel(self, id: int, /) -> abc.Channel | None:
        """Removes a channel from the cache."""
        raise NotImplementedError

    def get_message(self, id: int | None, /) -> Message | None:
        """Gets a message from the cache."""
        raise NotImplementedError

    def store_message(self, message: Message, /) -> None:
        """Stores a message in the cache."""
        raise NotImplementedError

    def remove_message(self, id: int, /) -> Message | None:
        """Removes a message from the cache."""
        raise NotImplementedError

    def get_sticker(self, id: int | None, /) -> Sticker | None:
        """Gets a sticker from the cache."""
        raise NotImplementedError

    def store_sticker(self, sticker: Sticker, /) -> None:
        """Stores a sticker in the cache."""
        raise NotImplementedError

    def remove_sticker(self, id: int, /) -> Sticker | None:
        """Removes a sticker from the cache."""
        raise NotImplementedError

    def get_soundboard_sound(self, id: int | None, /) -> SoundboardSound | None:
        """Gets a soundboard sound from the cache."""
        raise NotImplementedError

    def store_soundboard_sound(self, sound: SoundboardSound, /) -> None:
        """Stores a soundboard sound in the cache."""
        raise NotImplementedError

    def remove_soundboard_sound(self, id: int, /) -> SoundboardSound | None:
        """Removes a soundboard sound from the cache."""
        raise NotImplementedError

    def store_component(self, component: Component, /) -> None:
        """Stores a component in the cache."""
        raise NotImplementedError

    def remove_component(self, custom_id: str, /) -> Component | None:
        """Removes a component from the cache."""
        raise NotImplementedError

    def get_member(self, guild_id: int | None, id: int | None, /) -> Member | None:
        """Gets a member from the cache."""
        raise NotImplementedError

    def store_member(self, guild_id: int, member: Member, /) -> None:
        """Stores a member in the cache."""
        raise NotImplementedError

    def remove_member(self, guild_id: int, id: int, /) -> Member | None:
        """Removes a member from the cache."""
        raise NotImplementedError

    def get_thread(self, id: int | None, /) -> Thread | None:
        """Gets a thread from the cache."""
        raise NotImplementedError

    def store_thread(self, thread: Thread, /) -> None:
        """Stores a thread in the cache."""
        raise NotImplementedError

    def remove_thread(self, id: int, /) -> Thread | None:
        """Removes a thread from the cache."""
        raise NotImplementedError

    def get_channel_or_thread(self, id: int | None, /) -> abc.Channel | Thread | None:
        """A shortcut for :meth:`get_channel` or :meth:`get_thread`."""
        return self.get_channel(id) or self.get_thread(id)
