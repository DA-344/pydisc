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

from .asset import Asset
from .emoji import Emoji
from .color import Color
from .flags import Permissions
from .utils import _get_snowflake
from .mixins import Hashable
from .missing import MISSING, MissingOr

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "RoleColors",
    "RoleTags",
    "Role",
)


class RoleColors:
    """Represents a role colors."""

    def __init__(
        self,
        *,
        primary: Color,
        secondary: Color | None = None,
        tertiary: Color | None = None,
    ) -> None:
        self.primary: Color = primary
        """The primary color of the role."""
        self.secondary: Color | None = secondary
        """The secondary color of the role."""
        self.tertiary: Color | None = tertiary
        """The tertiary color of the role."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoleColors:
        primary = Color(data["primary_color"])
        secondary: Color | None = None
        tertiary: Color | None = None

        if sec_value := data.get("secondary_color"):
            secondary = Color(sec_value)
        if ter_value := data.get("tertiary_color"):
            tertiary = Color(ter_value)

        return RoleColors(
            primary=primary,
            secondary=secondary,
            tertiary=tertiary,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_color": self.primary.value,
            "secondary_color": self.secondary.value if self.secondary is not None else None,
            "tertiary_color": self.tertiary.value if self.tertiary is not None else None,
        }


class RoleTags:
    """Represents the tags of a role."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.bot_id: int | None = _get_snowflake("bot_id", data)
        """The bot ID that manages the role."""
        self.integration_id: int | None = _get_snowflake("integration_id", data)
        """The integration ID that manages the role."""
        self.subscription_listing_id: int | None = _get_snowflake("subscription_listing_id", data)
        """The subscription SKU ID this role is bound to."""

        self._premium_subscriber: MissingOr[None] = data.get("premium_subscriber", MISSING)
        self._available_for_purchase: MissingOr[None] = data.get("available_for_purchase", MISSING)
        self._guild_connections: MissingOr[None] = data.get("guild_connections", MISSING)

    @property
    def premium_subscriber(self) -> bool:
        """Whether this role is the guild's Booster role."""
        return self._premium_subscriber is None

    @property
    def available_for_purchase(self) -> bool:
        """Whether this role is available for purchase."""
        return self._available_for_purchase is None

    @property
    def guild_connections(self) -> bool:
        """Whether this role is a linked role."""
        return self._guild_connections is None


class Role(Hashable):
    """Represents a guild role."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The role ID."""
        self.name: str = data["name"]
        """The role name."""
        self.colors: RoleColors = RoleColors.from_dict(data["colors"])
        """The colors of this role."""
        self.hoisted: bool = data["hoist"]
        """Whether this role is hoisted."""
        self._icon: str | None = data.get("icon")
        self._unicode_emoji: str | None = data.get("unicode_emoji")
        self.position: int = data["position"]
        """The position of this role in the guild."""
        self.permissions: Permissions = Permissions(int(data["permissions"]))
        """THe permissions of this role."""
        self.managed: bool = data["managed"]
        """Whether this role is managed by an integration."""
        self.mentionable: bool = data["mentionable"]
        """Whether this role is mentionable by users."""
        self._flags: int = data.get("flags", 0)
        self.tags: RoleTags = RoleTags(data.get("tags", {}))
        """The tags of this role."""

    @property
    def icon(self) -> Asset | None:
        """Returns the icon of this role."""
        if self._icon is None:
            return None
        return Asset(
            route=f"role-icons/{self.id}/{self._icon}.png",
            key=self._icon,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @property
    def emoji(self) -> Emoji | None:
        """Returns the emoji of this role."""
        if self._unicode_emoji is None:
            return None
        return Emoji(
            self._unicode_emoji,
            id=None,
            animated=False,
        )
