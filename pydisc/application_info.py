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

from .flags import Permissions
from .asset import Asset
from .user import PartialUser
from .utils import _get_snowflake
from .mixins import Hashable
from .teams import Team
from .guild import PartialGuild, Guild

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "ApplicationInfo",
    "ApplicationInstallParams",
    "ApplicationIntegrationConfig",
)


class ApplicationInfo(Hashable):
    """Represents the available information from an application."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of this application."""
        self._cache: CacheProtocol = cache
        self.name: str = data["name"]
        """The application name."""
        self.description: str = data["description"]
        """The application description."""
        self._icon_hash: str | None = data.get("icon")
        self.rpc_origins: list[str] = data.get("rpc_origins", [])
        """The list of RPC origins (URLs) of this application."""
        self.public: bool = data["bot_public"]
        """Whether this bot is public."""
        self.requires_code_grant: bool = data["bot_require_code_grant"]
        """Whether the app's bot will join after fully completing the OAuth2 grant flow."""

        bot_data: dict[str, Any] | None = data.get("bot")
        self.bot: PartialUser | None = cache.get_user(_get_snowflake("id", bot_data or {}))
        """The bot user associated with this application."""

        if self.bot is None:
            self.bot = PartialUser.from_dict(bot_data, cache)
        else:
            if bot_data is not None:
                self.bot.__init__(bot_data, cache)

        self.terms_of_service_url: str | None = data.get("terms_of_service_url")
        """The terms of service url of this application."""
        self.privacy_policy_url: str | None = data.get("privacy_policy_url")
        """The privacy policy url of this application."""
        self.owner: PartialUser | None = PartialUser.from_dict(data.get("owner"), cache)
        """The owner of the application."""
        self.verify_key: str = data["verify_key"]
        """The hex encoded key for verification in interactions and the GameSDK."""
        self.team: Team | None = Team.from_dict(data.get("team"), cache)
        """The team the app belongs to."""
        self.guild_id: int | None = _get_snowflake("guild_id", data)
        """The guild associated with the app."""
        self.guild: PartialGuild | None = cache.get_guild(self.guild_id)
        """The partial guild associated with this application."""

        guild_data: dict[str, Any] | None = data.get("guild")
        if self.guild is None:
            self.guild = PartialGuild.from_dict(guild_data, cache)
        else:
            if guild_data is not None:
                self.guild.__init__(guild_data, cache)

        self.primary_sku_id: int | None = _get_snowflake("primary_sku_id", data)
        """The application's id of the SKU created in its game, if applicable."""
        self.slug: str | None = data.get("slug")
        """If this application is a game, the slug shown."""
        self._cover_image: str | None = data.get("cover_image")
        self._flags: int = data.get("flags", 0)
        self.approximate_guild_count: int | None = data.get("approximate_guild_count")
        """The approximate guild count where the application has been added to."""
        self.approximate_user_install_count: int | None = data.get("approximate_user_install_count")
        """The approximate user count who have added the application."""
        self.redirect_uris: list[str] = data.get("redirect_uris", [])
        """The redirect URIs of this application."""
        self.interactions_endpoint_url: str | None = data.get("interactions_endpoint_url")
        """The URL in which interactions are posted for this application."""
        self.role_connections_verification_url: str | None = data.get("role_connections_verification_url")
        """The URL in which role connections verifications are posted for this application."""
        self.event_webhooks_url: str | None = data.get("event_webhooks_url")
        """The URL in which webhook events are posted for this application."""
        self.event_webhook_types: list[str] = data.get("event_webhook_types", [])
        """The webhook events this application has subscribed to."""
        self.tags: list[str] = data.get("tags", [])
        """The application tags."""
        self.install_params: ApplicationInstallParams | None = ApplicationInstallParams.from_dict(data.get("install_params"))
        """The install parameters of this application."""
        self.custom_install_url: str | None = data.get("custom_install_url")
        """The custom insatll URL for this application."""
        self._integration_configs: dict[Literal["0", "1"], dict[str, Any]] = data.get("integration_types_config", {})

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> ApplicationInfo | None:
        if data is None:
            return None
        return ApplicationInfo(data, cache)

    @property
    def icon(self) -> Asset | None:
        """The application's icon."""
        if self._icon_hash is None:
            return None
        return Asset(
            route=f"app-icons/{self.id}/{self._icon_hash}.png",
            key=self._icon_hash,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @property
    def user_integration_config(self) -> ApplicationIntegrationConfig | None:
        """Returns the default settings for this application in a user-install context."""
        try:
            return ApplicationIntegrationConfig(self._integration_configs["1"])
        except KeyError:
            return None

    @property
    def guild_integration_config(self) -> ApplicationIntegrationConfig | None:
        """Returns thed default settings for this pplication in a guild-install context."""
        try:
            return ApplicationIntegrationConfig(self._integration_configs["0"])
        except KeyError:
            return None


class ApplicationInstallParams:
    """Represents an :class:`ApplicationInfo` install params."""

    def __init__(
        self,
        data: dict[str, Any],
    ) -> None:
        self.scopes: list[str] = data["scopes"]
        """The scopes authorized when the app is added."""
        self.permissions: Permissions = Permissions(int(data["permissions"]))
        """The permissions that the app will be granted once authorized."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ApplicationInstallParams | None:
        if data is None:
            return None
        return ApplicationInstallParams(data)


class ApplicationIntegrationConfig:
    """Represents the install config for certain integration type set in :attr:`ApplicationInfo.user_integration_config`
    and :attr:`ApplicationInfo.guild_integration_config`.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.install_params: ApplicationInstallParams | None = None
        """Represents the install params for the provided integration type."""

        try:
            self.install_params = ApplicationInstallParams(data["oauth2_install_params"])
        except KeyError:
            pass
