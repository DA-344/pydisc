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

from .abc import User as BaseUser
from .asset import Asset
from .collectibles import Collectibles
from .utils import _get_snowflake

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .guild import Guild

__all__ = (
    "PartialUser",
    "AvatarDecoration",
    "User",
    "PrimaryGuild",
)


class PartialUser(BaseUser):
    """Represents a partial user.
    """

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        self.discriminator: int = int(data["discriminator"])
        self.global_name: str | None = data.get("global_name")
        self.bot: bool = data.get("bot", False)
        self.system: bool = data.get("system", False)
        self._accent_color = None
        self._public_flags = 0
        self.avatar_decoration = None
        self.collectibles = None
        self.primary_guild = None
        self._avatar = data.get("avatar")
        self._banner = data.get("banner")

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Self | None:
        if data is None:
            return None
        return cls(data, cache)

    @property
    def cached(self) -> User | None:
        """Returns the cached version of this user."""
        return self._cache.get_user(self.id)


class User(PartialUser):
    """Represents a full user."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)

        self._accent_color = data.get("accent_color")
        self._public_flags = data.get("public_flags", 0)
        self.avatar_decoration = AvatarDecoration.from_dict(data.get("avatar_decoration_data"), cache)
        self.collectibles = Collectibles.from_dict(data.get("collectibles"), cache)
        self.primary_guild = PrimaryGuild.from_dict(data.get("primary_guild"), cache)

    def is_partial(self) -> bool:
        return False


class AvatarDecoration:
    """Represents a :attr:`abc.User.avatar_decoration`."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._asset: str = data["asset"]
        self._cache: CacheProtocol = cache
        self.sku_id: int = int(data["sku_id"])
        """The SKU ID of the avatar decoration."""

    @property
    def asset(self) -> Asset:
        """The asset of this decoration."""
        return Asset(
            route=f"avatar-decoration-presets/{self._asset}.png",
            key=self._asset,
            animated=True,
            cache=self._cache,
            format="png",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> AvatarDecoration | None:
        if data is None:
            return None
        return AvatarDecoration(data, cache)


class PrimaryGuild:
    """Represents a guild tag available at :attr:`abc.User.primary_guild`."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.guild_id: int | None = _get_snowflake("identity_guild_id", data)
        """The guild ID the tag points to."""
        self.enabled: bool | None = data.get("identity_enabled")
        """Whether the user shows the tag in their profile.

        If this is ``None``, the guild has changed its tag but the user has not adopted it
        yet.
        """
        self.tag: str | None = data.get("tag")
        """The guild tag."""
        self._badge: str | None = data.get("badge")

    @property
    def badge(self) -> Asset | None:
        """The tag badge asset."""
        if self._badge is None:
            return None
        return Asset(
            route=f"guild-tag-badges/{self.guild_id}/{self._badge}.png",
            key=self._badge,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @property
    def guild(self) -> Guild | None:
        """Returns the cached guild of this tag."""
        return self._cache.get_guild(self.guild_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> PrimaryGuild | None:
        if data is None:
            return None
        return PrimaryGuild(data, cache)
