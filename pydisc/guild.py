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
from typing import TYPE_CHECKING, Any

from .asset import Asset
from .channels import GuildChannel, StageChannel, TextChannel, Thread, VoiceChannel
from .enums import ChannelType
from .member import Member, VoiceState
from .mixins import Hashable
from .presences import Presence
from .role import Role
from .scheduled_event import ScheduledEvent
from .utils import parse_time

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "UnavailableGuild",
    "PartialGuild",
    "Guild",
)


class UnavailableGuild(Hashable):
    """Represents an unavailable guild."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.id: int = int(data["id"])
        """The ID of the guild."""
        self._unavailable: bool = data.get("unavailable", False)

    def is_available(self) -> bool:
        """Whether this guild is available."""
        return not self._unavailable

    def is_partial(self) -> bool:
        """Whether this guild is partial.

        If a guild is partial, some data may be missing or incorrect.
        """
        return True

    def _update(self, data: dict[str, Any]) -> None:
        if (un := data.get("unavailable")) is not None:
            self._unavailable = un


class PartialGuild(UnavailableGuild):
    """Represents a Discord guild."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data)
        self.name: str = data["name"]
        """The name of this guild."""

        self._icon: str | None = data.get("icon")
        self._icon_hash: str | None = data.get("icon_hash")
        self._splash: str | None = data.get("splash")
        self._discovery_splash: str | None = data.get("discovery_splash")

        self._cache: CacheProtocol = cache

    def _update(self, data: dict[str, Any]) -> None:
        super()._update(data)

        if (name := data.get("name")) is not None:
            self.name = name

        for key in ("icon", "icon_hash", "splash", "discovery_splash"):
            if key in data:
                setattr(self, f"_{key}", data[key])

    @property
    def _icon_str(self) -> str | None:
        return self._icon or self._icon_hash

    @property
    def icon(self) -> Asset | None:
        """Returns this guild's icon."""
        if self._icon_str is None:
            return None
        ext = "gif" if self._icon_str.startswith("a_") else "png"
        return Asset(
            route=f"icons/{self.id}/{self._icon_str}.{ext}",
            key=self._icon_str,
            animated=ext == "gif",
            cache=self._cache,
            format=ext,
        )

    @property
    def splash(self) -> Asset | None:
        """Returns this guild's splash."""
        if self._splash is None:
            return None
        return Asset(
            route=f"splash/{self.id}/{self._splash}.png",
            key=self._splash,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @property
    def discovery_splash(self) -> Asset | None:
        """Returns this guild's discovery splash."""
        if self._discovery_splash is None:
            return None
        return Asset(
            route=f"discovery-splashes/{self.id}/{self._discovery_splash}.png",
            key=self._discovery_splash,
            animated=False,
            cache=self._cache,
            format="png",
        )


class Guild(PartialGuild):
    """Represents a guild object."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)

        self._joined_at: datetime.datetime | None = parse_time(data.get("joined_at"))

        # cached things from Guild, received via gateway
        self._members_: dict[int, Member] = {}
        self._roles_: dict[int, Role] = {}
        self._channels_: dict[int, GuildChannel] = {}
        self._voice_states_: dict[int, VoiceState] = {}
        self._threads_: dict[int, Thread] = {}
        self._presences_: dict[int, Presence] = {}
        self._stages_: dict[int, StageChannel]
        self._events_: dict[int, ScheduledEvent] = {}

        self._member_count: int | None = data.get("member_count")
        self._large: bool | None = data.get("large")

    @property
    def joined_at(self) -> datetime.datetime | None:
        """When the current user has joined this guild, if applicable."""
        if self._joined_at is not None:
            # prefer the joined_at received from Guild Create
            return self._joined_at
        return self.me and self.me.joined_at

    def _update(self, data: dict[str, Any]) -> None:
        super()._update(data)

    @property
    def me(self) -> Member | None:
        """The current user's member object in this guild, if applicable."""
        return self._cache.client.user and self.get_member(self._cache.client.user.id)

    @property
    def members(self) -> list[Member]:
        """Returns the members of this guild."""
        return list(self._members_.values())

    @property
    def roles(self) -> list[Role]:
        """Returns the roles of this guild."""
        return list(self._roles_.values())

    @property
    def channels(self) -> list[GuildChannel | Thread]:
        """Returns all channels from this guild."""
        return list(self._channels_.values()) + self.threads + self.stage_channels

    @property
    def text_channels(self) -> list[TextChannel]:
        """Returns all text channels from this guild."""
        return [ch for ch in self._channels_.values() if ch.type in (ChannelType.text, ChannelType.announcement)]  # type: ignore

    @property
    def voice_channels(self) -> list[VoiceChannel]:
        """Returns all voice channels from this guild."""
        return [ch for ch in self._channels_.values() if ch.type is ChannelType.voice]  # type: ignore

    @property
    def stage_channels(self) -> list[StageChannel]:
        """Returns all stage channels from this guild."""
        return list(self._stages_.values())

    @property
    def threads(self) -> list[Thread]:
        """Returns all threads from this guild."""
        return list(self._threads_.values())

    def get_member(self, id: int, /) -> Member | None:
        """Gets a member from this guild with :attr:`Member.id` as ``id``, or :data:`None`."""
        return self._members_.get(id)

    def get_role(self, id: int, /) -> Role | None:
        """Gets a role from this guild with :attr:`Role.id` as ``id``, or :data:`None`."""
        return self._roles_.get(id)

    def get_channel(self, id: int, /) -> GuildChannel | None:
        """Gets a channel from this guild with :attr:`GuildChannel.id` as ``id``, or :data:`None`."""
        return self._channels_.get(id) or self._stages_.get(id)

    def get_thread(self, id: int, /) -> Thread | None:
        """Gets a thread from this guild with :attr:`Thread.id` as ``id``, or :data:`None`."""
        return self._threads_.get(id)

    def get_channel_or_thread(self, id: int, /) -> GuildChannel | Thread | None:
        """Gets a channel or thread from this guild, with :attr:`Channel.id` as ``id`` or :data:`None`."""
        return self.get_channel(id) or self.get_thread(id)

    def is_partial(self) -> bool:
        return False
