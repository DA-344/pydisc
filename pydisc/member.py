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

import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Self

from .flags import MemberFlags, PublicUserFlags
from .abc import Snowflake
from .asset import Asset
from .role import Role
from .object import Object
from .mixins import Hashable
from .user import AvatarDecoration, User
from .utils import parse_time, _get_snowflake

if TYPE_CHECKING:
    from .abc import Channel
    from .color import Color
    from .guild import Guild
    from .cache._types import CacheProtocol
    from .user import PrimaryGuild
    from .collectibles import Collectibles

__all__ = (
    "PartialMember",
    "Member",
    "VoiceState",
)


class PartialMember:
    """Represents a partial member from a :class:`Guild`."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, guild: Guild | None) -> None:
        self._roles: dict[int, Snowflake] = {}
        self._guild: Guild | None = guild
        self.joined_at: datetime.datetime | None = parse_time(data.get("joined_at"))
        """When this member joined the guild."""
        self.deaf: bool = data.get("deaf", False)
        """Whether this member is deafened in voice channels."""
        self.mute: bool = data.get("mute", False)
        """Whether this member is muted in voice channels."""
        self._flags: int = data.get("flags", 0)

        self._cache: CacheProtocol = cache

        for rid in data.get("roles", []):
            rid = int(rid)

            if self._guild:
                role = self._guild.get_role(rid)
            else:
                role = None

            if role is None:
                role = Object(id=rid, type=Role)

            self._roles[rid] = role

    def _update(self, data: dict[str, Any], guild: Guild | None) -> None:
        self._guild = guild

        for key in ("deaf", "mute"):
            if key in data:
                setattr(self, key, data[key] or False)

        if "joined_at" in data:
            self.joined_at = parse_time(data["joined_at"])

        if (flags := data.get("flags")) is not None:
            self._flags = flags

        for rid in data.get("roles", []):
            rid = int(rid)

            if self._guild:
                role = self._guild.get_role(rid)
            else:
                role = None

            if role is None:
                role = Object(id=rid, type=Role)

            self._roles[rid] = role

    @property
    def guild(self) -> Guild | None:
        """The guild this member is from."""
        return self._guild

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol, guild: Guild | None) -> Self | None:
        if data is None:
            return None
        return cls(data, cache, guild)

    def is_partial(self) -> bool:
        """Whether this member is partial.

        If a member is partial, some data may be missing or incorrect.
        """
        return True


class Member(PartialMember, Hashable):
    """Represents a member from a :class:`Guild`.

    Although this is not a :class:`User`, it has utility properties for accessing
    user attributes.
    """

    if TYPE_CHECKING:
        _guild: Guild

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, guild: Guild) -> None:
        super().__init__(data, cache, guild)

        # this key will always be present, either because received via the API or because
        # it is available elsewhere (like in message create and update, where the author key is
        # the user in here)
        user_data: dict[str, Any] = data["user"]
        user_id: int | None = _get_snowflake("id", user_data)
        self.user: User = cache.get_user(user_id)  # type: ignore
        """The user that is bound to this member."""

        if self.user is None:  # type: ignore
            self.user = User(user_data, cache)
            cache.store_user(self.user)
        else:
            self.user._update(user_data)

        self.nick: str | None = data.get("nick")
        """The nickname of the user in this guild."""
        self._avatar: str | None = data.get("avatar")
        self._banner: str | None = data.get("banner")
        self.premium_since: datetime.datetime | None = parse_time(data.get("premium_since"))
        """Since when this member has been boosting the guild."""
        self.pending: bool = data.get("pending", False)
        """Whether this member has not yet completed the Membership Screening"""
        self._permissions: int = int(data.get("permissions", 0))
        self.timed_out_until: datetime.datetime | None = parse_time(data.get("communication_disabled_until"))
        """When the user's timeout will expire.

        To check whether a user is still timed out, you should use :meth:`is_timed_out`.
        """
        self.guild_avatar_decoration: AvatarDecoration | None = AvatarDecoration.from_dict(data.get("avatar_decoration_data"), cache)
        """The guild avatar decoration data of this member."""

    def _update(self, data: dict[str, Any], guild: Guild | None) -> None:
        super()._update(data, guild)

        if (user := data.get("user")) is not None:
            self.user._update(user)

        for key in ("nick",):
            if key in data:
                setattr(self, key, data[key])

        for key in ("avatar", "banner"):
            if key in data:
                setattr(self, f"_{key}", data[key])

        for key in ("pending",):
            if key in data:
                setattr(self, key, data[key] or False)

        for key, attr, factory in (
            ("premium_since", "", parse_time,),
            ("communication_disabled_until", "timed_out_until", parse_time),
            ("avatar_decoration_data", "guild_avatar_decoration", partial(AvatarDecoration.from_dict, cache=self._cache)),
        ):
            attr = attr or key
            if key in data:
                setattr(self, attr, factory(data[key]))

        if "permissions" in data:
            self._permissions = int(data["permissions"] or 0)

    def is_timed_out(self) -> bool:
        """Whether this member is timed out."""
        if self.timed_out_until is None:
            return False
        return self.timed_out_until < datetime.datetime.now(datetime.timezone.utc)

    @property
    def guild(self) -> Guild:
        return self._guild

    @property
    def id(self) -> int:
        """The ID of this member."""
        return self.user.id

    @property
    def avatar_decoration(self) -> AvatarDecoration | None:
        """A shortcut for :attr:`Member.user.avatar_decoration <User.avatar_decoration>`."""
        return self.user.avatar_decoration

    @property
    def display_avatar_decoration(self) -> AvatarDecoration | None:
        """Returns the display avatar decoration of this member."""
        return self.guild_avatar_decoration or self.avatar_decoration

    @property
    def guild_avatar(self) -> Asset | None:
        """The per-guild avatar of this member in its guild."""
        if self._avatar is None:
            return None
        ext = "gif" if self._avatar.startswith("a_") else "png"
        return Asset(
            route=f"guilds/{self.guild.id}/users/{self.id}/avatars/{self._avatar}.{ext}",
            key=self._avatar,
            animated=ext == "gif",
            cache=self._cache,
            format=ext,
        )

    @property
    def guild_banner(self) -> Asset | None:
        """The per-guild banner of this member in its guild."""
        if self._banner is None:
            return None
        ext = "gif" if self._banner.startswith("a_") else "png"
        return Asset(
            route=f"guilds/{self.guild.id}/users/{self.id}/banners/{self._banner}.{ext}",
            key=self._banner,
            animated=ext == "gif",
            cache=self._cache,
            format=ext,
        )

    @property
    def avatar(self) -> Asset | None:
        """A shortcut for :attr:`Member.user.avatar <User.avatar>`."""
        return self.user.avatar

    @property
    def default_avatar(self) -> Asset:
        """A shortcut for :attr:`Member.user.default_avatar <User.default_avatar>`."""
        return self.user.default_avatar

    @property
    def banner(self) -> Asset | None:
        """A shortcut for :attr:`Member.user.banner <User.banner>`."""
        return self.user.banner

    @property
    def display_banner(self) -> Asset | None:
        """Returns the display banner of this member."""
        return self.guild_banner or self.banner

    @property
    def display_avatar(self) -> Asset:
        """Returns the display avatar of this member."""
        return self.guild_avatar or self.avatar or self.default_avatar

    @property
    def accent_color(self) -> Color | None:
        """A shortcut for :attr:`Member.user.accent_color <User.accent_color>`."""
        return self.user.accent_color

    @property
    def primary_guild(self) -> PrimaryGuild | None:
        """A shortcut for :attr:`Member.user.primary_guild <User.primary_guild>`."""
        return self.user.primary_guild

    @property
    def collectibles(self) -> Collectibles | None:
        """A shortcut for :attr:`Member.user.collectibles <User.collectibles>`."""
        return self.user.collectibles

    @property
    def discriminator(self) -> str:
        """A shortcut for :attr:`Member.user.discriminator <User.discriminator>`."""
        return self.user.discriminator

    @property
    def bot(self) -> bool:
        """A shortcut for :attr:`Member.user.bot <User.bot>`."""
        return self.user.bot

    @property
    def system(self) -> bool:
        """A shortcut for :attr:`Member.user.system <User.system>`."""
        return self.user.system

    @property
    def public_flags(self) -> PublicUserFlags:
        """A shortcut for :attr:`Member.user.public_flags <User.public_flags>`."""
        return self.user.public_flags

    @property
    def name(self) -> str:
        """A shortcut for :attr:`Member.user.name <User.name>`."""
        return self.user.name

    @property
    def global_name(self) -> str | None:
        """A shortcut for :attr:`Member.user.global_name <User.global_name>`."""
        return self.user.global_name

    @property
    def display_name(self) -> str:
        """Returns the display name of this member."""
        return self.nick or self.user.display_name

    def is_partial(self) -> bool:
        return False


class VoiceState:
    """Represents a member's voice state."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.guild_id: int | None = _get_snowflake("guild_id", data)
        """The guild ID this voice state is for."""
        self.channel_id: int | None = _get_snowflake("channel_id", data)
        """The channel ID this voice state is for."""
        self.user_id: int = int(data["user_id"])
        """The ID of the user this state is from."""
        self.session_id: str | None = data.get("session_id")
        """The session ID of the voice state."""
        self.deaf: bool = data.get("deaf", False)
        """Whether this user is deafened by the guild."""
        self.mute: bool = data.get("mute", False)
        """Whether this user is muted by the guild."""
        self.self_deaf: bool = data.get("self_deaf", False)
        """Whether the user is deafened by their own accord."""
        self.self_mute: bool = data.get("self_mute", False)
        """Whether the user is muted by their own accord."""
        self.self_stream: bool = data.get("self_stream", False)
        """Whether the user is currently streaming with the "Go Live" feature."""
        self.self_video: bool = data.get("self_video", False)
        """Whether the user is currently using their camera."""
        self.suppress: bool = data.get("suppress", False)
        """Whether the user's speak permission is denied."""
        self.requested_to_speak_at: datetime.datetime | None = parse_time(data.get("request_to_speak_timestamp"))
        """When this user requested to speak, in a stage channel."""

        self._cache: CacheProtocol = cache

    def _update(self, data: dict[str, Any]) -> None:
        for key in ("guild_id", "channel_id"):
            if key in data:
                setattr(self, key, _get_snowflake(key, data))

        if (session := data.get("session_id")) is not None:
            self.session_id = session

        for key in ("deaf", "mute", "self_deaf", "self_mute", "self_stream", "self_video", "suppress"):
            if key in data:
                setattr(self, key, data[key] or False)

        if "requested_to_speak_timestamp" in data:
            self.requested_to_speak_at = parse_time(data["requested_to_speak_timestamp"])

    @property
    def guild(self) -> Guild | None:
        """The guild this voice state is for."""
        return self._cache.get_guild(self.guild_id)

    @property
    def channel(self) -> Channel | None:
        """The channel this voice state is for."""
        return self._cache.get_channel(self.channel_id)

    @property
    def user(self) -> User | None:
        """The user this voice state is from."""
        return self._cache.get_user(self.user_id)

    @property
    def member(self) -> Member | None:
        """The member this voice state is from, in case this belongs to a guild."""
        return self.guild and self.guild.get_member(self.user_id)
