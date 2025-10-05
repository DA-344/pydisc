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

from collections.abc import Callable
import datetime
from typing import TYPE_CHECKING, Any

from pydisc.abc import Channel, User
from pydisc.enums import ChannelType, PermissionOverwriteType, try_enum
from pydisc.flags import ChannelFlags, Permissions
from pydisc.object import Object
from pydisc.overwrites import PermissionOverwrite
from pydisc.role import Role
from pydisc.utils import parse_time, _get_snowflake

if TYPE_CHECKING:
    from pydisc.cache._types import CacheProtocol
    from pydisc.guild import Guild
    from pydisc.message import Message

__all__ = (
    "PartialChannel",
    "GuildChannel",
)


class PartialChannel(Channel):
    """Represents a partial channel."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of this channel."""
        self.guild_id: int = int(data["guild_id"])
        """The guild ID the channel is from."""
        self._type: ChannelType = try_enum(ChannelType, data["type"])
        self.name: str = data["name"]
        """The name of this channel."""
        self._cache: CacheProtocol = cache

    @property
    def type(self) -> ChannelType:
        """The type of this channel."""
        return self._type

    @property
    def guild(self) -> Guild | None:
        """The guild this channel belongs to."""
        return self._cache.get_guild(self.guild_id)

    @property
    def cached(self) -> Channel | None:
        """Returns the cached version of this channel."""
        return self._cache.get_channel(self.id)


class GuildChannel(PartialChannel):
    """A protocol that abstracts out :class:`Guild`-bound channels."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)
        self.topic: str | None = data.get("topic")
        """The topic of this channel."""
        self.nsfw: bool = data.get("nsfw", False)
        """Whether this channel is marked as NSFW."""
        self.slowmode_delay: int | None = data.get("rate_limit_per_user")
        """The amount of seconds users must wait to send another message.

        This is treated as disabled when its value is ``None`` or ``0``.
        """
        self.parent_id: int | None = _get_snowflake("parent_id", data)
        """The parent (aka category) ID of this channel."""
        self.last_message_id: int | None = _get_snowflake("last_message_id", data)
        """The ID of the last message sent or last thread created in this channel."""
        self.last_pinned_at: datetime.datetime | None = parse_time(data.get("last_pin_timestamp"))
        """The timestamp of when the last message was pinned."""
        self.position: int = data["position"]
        """The position of this channel in the guild."""
        self._overwrites: list[PermissionOverwrite] = PermissionOverwrite.from_dict_array(data.get("permission_overwrites", []), self.guild_id)
        self._flags: int = data.get("flags", 0)

    @property
    def flags(self) -> ChannelFlags:
        """The flags of this channel."""
        return ChannelFlags(self._flags)

    @property
    def overwrites(self) -> dict[Object | Role | User, PermissionOverwrite]:
        """Returns a mapping of {Snowflake: PermissionOverwrite} denoting the available
        overwrites of this channel.
        """
        ret: dict[Object | Role | User, PermissionOverwrite] = {}

        get_role = self.guild.get_role if self.guild else (lambda rid: Object(id=rid, type=Role))
        get_member = self.guild.get_member if self.guild else (lambda mid: Object(id=mid, type=User))

        for ow in self._overwrites:
            target = None
            ttype = Role if ow.is_role() else User

            if ow.is_role():
                target = get_role(ow.id)
            elif ow.is_member():
                target = get_member(ow.id)

            if target is None:
                target = Object(id=ow.id, type=ttype)

            ret[target] = ow
        return ret

    def overwrites_for(self, obj: Role | User | Object) -> PermissionOverwrite:
        """Returns this channel-specific overwrites for the provided object.
        """

        pred: Callable[[PermissionOverwrite], bool]

        if isinstance(obj, User) or (isinstance(obj, Object) and issubclass(obj.type, User)):
            pred = lambda p: p.is_member()
            typ = PermissionOverwriteType.member
        elif isinstance(obj, Role) or (isinstance(obj, Object) and issubclass(obj.type, Role)):
            pred = lambda p: p.is_role()
            typ = PermissionOverwriteType.role
        else:
            pred = lambda p: True
            typ = PermissionOverwriteType("unknown")

        for ow in filter(pred, self._overwrites):
            if ow.id == obj.id:
                return ow
        return PermissionOverwrite(
            id=obj.id,
            type=typ,
            allow=Permissions(0),
            deny=Permissions(0),
        )

    def can_send_message(self) -> bool:
        """Whether the current user can send messages in this channel."""
        if self.guild is not None:
            me = self.guild.me
        else:
            me = Object(id=self._cache.client.user.id, type=User)
        permissions = self.overwrites_for(me)
        return Permissions.send_messages in permissions.allow

    @property
    def last_message(self) -> Message | None:
        """The cached version of :attr:`last_message_id`."""
        return self._cache.get_message(self.last_message_id)
