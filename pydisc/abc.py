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

from collections.abc import Sequence
import datetime
from typing import TYPE_CHECKING

from .missing import MISSING, MissingOr
from .asset import Asset
from .enums import ChannelType
from .utils import checkable_protocol, Protocol, snowflake_to_time
from .flags import MessageFlags, PublicUserFlags
from .color import Color
from .http import handle_message_parameters

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .user import AvatarDecoration, PrimaryGuild, User as FullUser
    from .collectibles import Collectibles
    from .message import PartialMessage, MessageReference
    from .embed import Embed
    from .file import File
    from .allowed_mentions import AllowedMentions
    from .components import Component
    from .poll import Poll
    from .message import PartialMessage, MessageReference
    from .guild import Guild

__all__ = (
    "Snowflake",
    "Channel",
    "Mentionable",
    "User",
    "Messageable",
)


@checkable_protocol
class Snowflake(Protocol):
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """Returns when the snowflake was created based off the :attr:`id`."""
        return snowflake_to_time(self.id)


@checkable_protocol
class Channel(Snowflake):
    type: ChannelType
    """The type of this channel."""
    guild: Guild | None
    """The guild this channel is bound to"""


@checkable_protocol
class Mentionable(Snowflake):
    def _get_mention_string(self) -> str:
        raise NotImplementedError(f"mention property is not implemented for {self.__class__.__name__!r}")

    @property
    def mention(self) -> str:
        """Returns the string that allows to mention this entity."""
        return self._get_mention_string().format(id=self.id)


@checkable_protocol
class User(Mentionable):
    id: int
    """The ID of the user."""
    name: str
    """The name of the user."""
    discriminator: int
    """The discriminator of the user. This is ``0`` if the user has migrated to the pomelo rollout."""
    global_name: str | None
    """The global name of this user."""
    bot: bool
    """Whether this user is a bot."""
    system: bool
    """Whether the user is an official Discord System user."""
    _accent_color: int | None
    _public_flags: int
    avatar_decoration: AvatarDecoration | None
    """The user avatar decoration."""
    collectibles: Collectibles | None
    """The user collectibles."""
    primary_guild: PrimaryGuild | None
    """The primary guild tag of the user."""
    _avatar: str | None
    _banner: str | None
    _cache: CacheProtocol

    @property
    def display_name(self) -> str:
        """Returns the display name of this user."""
        return self.global_name or self.name

    def _get_mention_string(self) -> str:
        return "<@{id}>"

    def mentioned_in(self, message: Message) -> bool:
        """Whether this user was mentioned in a message."""
        if message.content:
            return self.mention in message.content
        return self.id in message.raw_mentions

    @property
    def public_flags(self) -> PublicUserFlags:
        """The user public flags."""
        return PublicUserFlags(self._public_flags)

    @property
    def accent_color(self) -> Color | None:
        """The user accent color."""
        if self._accent_color is None:
            return None
        return Color(self._accent_color)

    @property
    def avatar(self) -> Asset | None:
        """The avatar of this user."""
        if self._avatar is None:
            return None
        ext = "gif" if self._avatar.startswith("a_") else "png"
        return Asset(
            route=f"avatars/{self.id}/{self._avatar}.{ext}",
            key=self._avatar,
            animated=self._avatar.startswith("a_"),
            cache=self._cache,
            format=ext,
        )

    @property
    def banner(self) -> Asset | None:
        """The banner of this user."""
        if self._banner is None:
            return None
        ext = "gif" if self._banner.startswith("a_") else "png"
        return Asset(
            route=f"banners/{self.id}/{self._banner}.{ext}",
            key=self._banner,
            animated=self._banner.startswith("a_"),
            cache=self._cache,
            format=ext,
        )

    def is_partial(self) -> bool:
        """Whether this user is partial.

        If a user is partial, some data may be missing or incorrect.
        """
        return True

    @property
    def migrated(self) -> bool:
        """Whether the user has migrated to the pomelo username system."""
        return self.discriminator == 0

    async def fetch(self) -> FullUser:
        """Fetches the current user."""
        return await self._cache.client.fetch_user(self.id)


class Messageable(Protocol):
    """An abstract method for sending messages to a destination."""

    _cache: CacheProtocol

    async def _get_channel(self) -> Snowflake:
        raise NotImplementedError

    async def send(
        self,
        content: MissingOr[str] = MISSING,
        *,
        tts: bool = False,
        embeds: MissingOr[Sequence[Embed]] = MISSING,
        files: MissingOr[Sequence[File]] = MISSING,
        stickers: MissingOr[Sequence[Snowflake]] = MISSING,
        nonce: MissingOr[int | str] = MISSING,
        allowed_mentions: MissingOr[AllowedMentions] = MISSING,
        reference: MissingOr[PartialMessage | MessageReference] = MISSING,
        components: MissingOr[Sequence[Component]] = MISSING,
        suppress_embeds: MissingOr[bool] = MISSING,
        enforce_nonce: MissingOr[bool] = MISSING,
        poll: MissingOr[Poll] = MISSING,
        silent: MissingOr[bool] = MISSING,
    ) -> Message:
        if reference is not MISSING:
            reference = reference.to_reference()

        channel = await self._get_channel()
        client = self._cache.client
        http = client.http

        flags = MessageFlags(0)

        if suppress_embeds:
            flags |= MessageFlags.suppress_embeds
        if silent:
            flags |= MessageFlags.suppress_notifications
        if any(c.is_v2() for c in (components or [])):
            flags |= MessageFlags.components_v2

        with handle_message_parameters(
            content=content,
            tts=tts,
            embeds=embeds,
            files=files,
            stickers=stickers,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=reference,
            components=components,
            flags=flags,
            poll=poll,
            enforce_nonce=enforce_nonce,
            cache=self._cache,
        ) as params:
            data = await http.send_message(channel.id, params=params)

        return self._cache._create_message(data)
