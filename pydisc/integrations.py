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

from .enums import IntegrationType, IntegrationExpireBehavior, try_enum
from .mixins import Hashable
from .utils import _get_snowflake, parse_time
from .user import User

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .guild import Guild
    from .role import Role

__all__ = (
    "IntegrationAccount",
    "PartialIntegration",
    "Integration",
    "IntegrationApplication",
)


class IntegrationAccount(Hashable):
    """Represents an :class:`Integration` or :class:`PartialIntegration` ``account``."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The integration account ID."""
        self.name: str = data["name"]
        """The integration account name."""


class PartialIntegration(Hashable):
    """Represents a partial :class:`Integration`."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The ID of the integration."""
        self.name: str = data["name"]
        """The integration name."""
        self.type: IntegrationType = try_enum(IntegrationType, data["type"])
        """The integration type."""
        self.enabled: bool = data["enabled"]
        """Whether this integration is enabled."""
        self.account: IntegrationAccount = IntegrationAccount(data["account"], cache)
        """The integration account."""
        self.application_id: int | None = _get_snowflake("application_id", data)
        """The application ID for this integration."""

    def is_partial(self) -> bool:
        """Whether this integration is partial.

        If an integration is partial, some data may be missing or incorrect.
        """
        return True


class Integration(PartialIntegration):
    """Represents an integration."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, guild: Guild) -> None:
        super().__init__(data, cache)

        self._guild: Guild = guild
        self.syncing: bool = data.get("syncing", False)
        """Whether the integration is syncing."""
        self.role_id: int | None = _get_snowflake("role_id", data)
        """The role ID linked to this integration."""
        self.enable_emoticons: bool = data.get("enable_emoticons", False)
        """Whether this integration syncs its emoticons.

        Only applicable if :attr:`type` is :attr:`IntegrationType.twitch`.
        """
        self.expire_behavior: IntegrationExpireBehavior | None = None
        """The expire behavior for expiring subscribers."""

        if expbh_data := data.get("expire_behavior"):
            self.expire_behavior = try_enum(IntegrationExpireBehavior, expbh_data)

        self.expire_grace_period: int | None = data.get("expire_grace_period")
        """The grace period (in days) before expiring subscribers."""
        self.user: User | None = User.from_dict(data.get("user"), cache)
        """The user of this integration."""
        self.synced_at: datetime.datetime | None = parse_time(data.get("synced_at"))
        """When this integration was last synced."""
        self.subscriber_count: int | None = data.get("subscriber_count")
        """The subscriber count of this integration."""
        self.revoked: bool = data.get("revoked", False)
        """Whether this integration has been revoked."""
        self.application: IntegrationApplication | None = IntegrationApplication.from_dict(data.get("application"), cache)
        """The bot/OAuth2 application for this integration.

        Only applicable if :attr:`type` if :attr:`IntegrationType.discord`.
        """
        self.scopes: list[str] = data.get("scopes", [])
        """The scopes of this integration."""

    @property
    def role(self) -> Role | None:
        """Returns the cached version of this role."""
        if self.role_id is None:
            return None
        return self._guild.get_role(self.role_id)

    def is_partial(self) -> bool:
        return False


class IntegrationApplication(Hashable):
    """Represents an :class:`Integration` application."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the app."""
        self.name: str = data["name"]
        """The name of the app."""
        self.description: str = data["description"]
        """The description of the app."""
        self.bot: User | None = User.from_dict(data.get("bot"), cache)
        """The bot associated with this application."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> IntegrationApplication | None:
        if data is None:
            return None
        return IntegrationApplication(data, cache)
