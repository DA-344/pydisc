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
from typing import TYPE_CHECKING, Any, Literal, overload

from .abc import Channel
from .object import Object
from .missing import MissingOr, MISSING
from .mixins import Hashable
from .enums import AutoModEventType, AutoModTriggerType, AutoModKeywordPresetType, AutoModActionType, try_enum

if TYPE_CHECKING:
    from . import abc
    from .user import User
    from .guild import Guild
    from .role import Role
    from .cache._types import CacheProtocol

__all__ = (
    "AutoModTriggerMetadata",
    "AutoModAction",
    "PartialAutoModRule",
    "AutoModRule",
)


class AutoModTriggerMetadata:
    """Represents the trigger metadata for an auto mod rule.
    """

    @overload
    def __init__(
        self,
        *,
        keywords: list[str],
        regex_patterns: MissingOr[list[str]] = ...,
        allow: MissingOr[list[str]] = ...,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        keywords: MissingOr[list[str]] = ...,
        regex_patterns: list[str],
        allow: MissingOr[list[str]] = ...,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        keyword_presets: list[AutoModKeywordPresetType],
        allow: MissingOr[list[str]] = MISSING,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        mention_limit: int,
        mention_raid_protection: MissingOr[bool] = ...,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        mention_limit: MissingOr[int] = ...,
        mention_raid_protection: bool,
    ) -> None: ...

    def __init__(
        self,
        *,
        keywords: MissingOr[list[str]] = MISSING,
        regex_patterns: MissingOr[list[str]] = MISSING,
        keyword_presets: MissingOr[list[AutoModKeywordPresetType]] = MISSING,
        allow: MissingOr[list[str]] = MISSING,
        mention_limit: MissingOr[int] = MISSING,
        mention_raid_protection: MissingOr[bool] = MISSING,
    ) -> None:
        unique = (keywords or regex_patterns, keyword_presets, mention_limit or mention_raid_protection)
        if sum(bool(u) for u in unique) > 1:
            raise ValueError(
                "You can only pass a defined combination of keywords to AutoModTriggerMetadata:",
                "keywords or regex_patterns, and allow;",
                "keyword_presets, and allow;"
                "mention_limit or mention_raid_protection."
            )

        self.keywords: list[str] = keywords or []
        """The substrings that will be searched for in messages content."""
        self.regex_patterns: list[str] = regex_patterns or []
        """The Rust-like regex patterns that will be matched against messages content."""
        self.keyword_presets: list[AutoModKeywordPresetType] = keyword_presets or []
        """The keyword presets types to enable that will work as predefined :attr:`keywords`."""
        self.allow: list[str] = allow or []
        """The list of allowed strings that will bypass :attr:`keywords`, :attr:`regex_patterns`, and :attr:`keyword_presets`."""
        self.mention_limit: int = mention_limit or 0
        """The maximum amount of unique mentions allowed per message."""
        self.mention_raid_protection: bool = mention_raid_protection or False
        """Whether to automatically detect mention raids."""

    def to_dict(self, for_type: AutoModTriggerType) -> dict[str, Any] | None:
        if for_type in (AutoModTriggerType.keyword, AutoModTriggerType.member_profile):
            return {
                "keyword_filter": self.keywords,
                "regex_patterns": self.regex_patterns,
                "allow_list": self.allow,
            }
        elif for_type is AutoModTriggerType.keyword_preset:
            return {
                "presets": [p.value for p in self.keyword_presets],
                "allow_list": self.allow,
            }
        elif for_type is AutoModTriggerType.mention_spam:
            return {
                "mention_total_limit": self.mention_limit,
                "mention_raid_protection_enabled": self.mention_raid_protection,
            }
        else:
            return None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AutoModTriggerMetadata | None:
        if data is None:
            return None

        keywords = data.get("keyword_filter", MISSING)
        regex_patterns = data.get("regex_patterns", MISSING)
        keyword_presets = [try_enum(AutoModKeywordPresetType, kp) for kp in data.get("keyword_presets", [])]
        allow = data.get("allow_list", MISSING)
        mention_limit = data.get("mention_total_limit", MISSING)
        mention_raid_protection = data.get("mention_raid_protection_enabled", MISSING)
        return AutoModTriggerMetadata(
            keywords=keywords,
            regex_patterns=regex_patterns,
            keyword_presets=keyword_presets,
            allow=allow,
            mention_limit=mention_limit,
            mention_raid_protection=mention_raid_protection,
        )  # type: ignore


class AutoModAction:
    """Represents an auto mod rule action, done when it is triggered."""

    @overload
    def __init__(
        self,
        *,
        type: Literal[AutoModActionType.send_alert_message],
        channel_id: int,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        type: Literal[AutoModActionType.timeout],
        timeout_duration: datetime.timedelta,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        type: Literal[AutoModActionType.block_member_interaction],
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        type: Literal[AutoModActionType.block_message],
        custom_message: MissingOr[str] = ...,
    ) -> None: ...

    def __init__(
        self,
        *,
        type: AutoModActionType,
        channel_id: MissingOr[int] = MISSING,
        timeout_duration: MissingOr[datetime.timedelta] = MISSING,
        custom_message: MissingOr[str] = MISSING,
    ) -> None:
        p_sum = sum(bool(p) for p in (channel_id, timeout_duration))
        if p_sum > 1:
            raise ValueError("only up to one parameter other from type can be passed per AutoModAction instance")
        if p_sum <= 0:  # doubtful it ends up being negative but, check anyways
            raise ValueError("you must provide a parameter other than type")

        self.type: AutoModActionType = type
        """The type of auto mod action."""

        if type is AutoModActionType.send_alert_message and channel_id is MISSING:
            raise ValueError("when type is send_alert_message, you must provide a channel_id")
        elif type is AutoModActionType.timeout and timeout_duration is MISSING:
            raise ValueError("when type is timeout, you must provide a timeout_duration")

        self.channel_id: int | None = channel_id or None
        """The channel ID in which the messages will be sent.

        Only applicable if :attr:`type` is :attr:`AutoModActionType.send_alert_message`.
        """
        self.timeout_duration: datetime.timedelta | None = timeout_duration or None
        """The timeout duration applied to the user that triggered the auto mod rule.

        Only applicable if :attr:`type` is :attr:`AutoModActionType.timeout`.
        """
        self.custom_message: str | None = custom_message or None
        """The custom block message shown when the message is blocked.

        Only applicable if :attr:`type` is :attr:`AutoModActionType.block_message`.
        """

    def to_dict(self) -> dict[str, Any]:
        if self.type is AutoModActionType.block_message and self.custom_message is not None:
            metadata = {"custom_message": self.custom_message}
        elif self.type is AutoModActionType.timeout:
            assert self.timeout_duration is not None
            metadata = {"duration_seconds": int(self.timeout_duration.total_seconds())}
        elif self.type is AutoModActionType.send_alert_message:
            assert self.channel_id is not None
            metadata = {"channel_id": self.channel_id}
        else:
            metadata = None

        return {
            "type": self.type.value,
            "metadata": metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoModAction:
        typ = try_enum(AutoModActionType, data["type"])

        if typ is AutoModActionType.send_alert_message:
            channel_id = int(data["metadata"]["channel_id"])
            return AutoModAction(type=typ, channel_id=channel_id)
        elif typ is AutoModActionType.block_message:
            custom_message = data.get("metadata", {}).get("custom_message", MISSING)
            return AutoModAction(type=typ, custom_message=custom_message)
        elif typ is AutoModActionType.timeout:
            duration = data["metadata"]["duration_seconds"]
            return AutoModAction(type=typ, timeout_duration=datetime.timedelta(seconds=duration))
        return AutoModAction(type=typ)


class PartialAutoModRule:
    """Represents a partial auto moderation rule."""

    def __init__(
        self,
        *,
        name: str,
        event_type: AutoModEventType,
        trigger_type: AutoModTriggerType,
        trigger_metadata: AutoModTriggerMetadata | None,
        actions: list[AutoModAction],
        enabled: bool = False,
        exempt_roles: MissingOr[list[abc.Snowflake]] = MISSING,
        exempt_channels: MissingOr[list[abc.Snowflake]] = MISSING,
    ) -> None:
        self.name: str = name
        """The name of the auto mod rule."""
        self.event_type: AutoModEventType = event_type
        """The event that triggers this auto mod rule."""
        self.trigger_type: AutoModTriggerType = trigger_type
        """The trigger filter for this auto mod rule."""
        self.trigger_metadata: AutoModTriggerMetadata | None = trigger_metadata
        """The trigger extra data filtering."""
        self.actions: list[AutoModAction] = actions
        """The list of actions done when the auto mod is fully triggered."""
        self.enabled: bool = enabled
        """Whether this auto mod rule is enabled."""
        self.exempt_roles: set[int] = {r.id for r in exempt_roles or []}
        """The set of exempt role IDs of this auto mod rule."""
        self.exempt_channels: set[int] = {c.id for c in exempt_channels or []}
        """The set of exempt channel IDs of this auto mod rule."""

    def is_exempt(self, object: abc.Snowflake, /) -> bool:
        """Whether ``object`` is exempt of this auto mod rule."""
        return object.id not in self.exempt_roles and object.id not in self.exempt_channels

    def is_partial(self) -> bool:
        """Whether this auto mod rule is partial.

        If an auto mod rule is partial, some data may be missing or incorrect.
        """
        return True

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "name": self.name,
            "event_type": self.event_type.value,
            "trigger_type": self.trigger_type.value,
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
        }

        if self.trigger_metadata is not None:
            pd["trigger_metadata"] = self.trigger_metadata.to_dict(self.trigger_type)
        if self.exempt_roles:
            pd["exempt_roles"] = list(self.exempt_roles)
        if self.exempt_channels:
            pd["exempt_channels"] = list(self.exempt_channels)
        return pd


class AutoModRule(PartialAutoModRule, Hashable):
    """Represents an auto moderation rule from a guild."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        super().__init__(
            name=data["name"],
            event_type=try_enum(AutoModEventType, data["event_type"]),
            trigger_type=try_enum(AutoModTriggerType, data["trigger_type"]),
            trigger_metadata=AutoModTriggerMetadata.from_dict(data.get("trigger_metadata")),
            actions=[AutoModAction.from_dict(a) for a in data["actions"]],
            enabled=data["enabled"],
            exempt_roles=list(map(lambda i: Object(id=int(i), type=Channel), data["exempt_roles"])),
            exempt_channels=list(map(lambda i: Object(id=int(i), type=Channel), data["exempt_channels"])),
        )

        self.guild_id: int = int(data["guild_id"])
        """The guild ID the auto mod rule is part from."""
        self.id: int = int(data["id"])
        """The ID of this rule."""
        self.creator_id: int = int(data["creator_id"])
        """The ID of the user that created this rule."""

    def is_partial(self) -> bool:
        return False

    @property
    def creator(self) -> User | None:
        """The cached version of the :attr:`creator_id`."""
        return self._cache.get_user(self.creator_id)

    @property
    def guild(self) -> Guild | None:
        """The cached version of the :attr:`guild_id`."""
        return self._cache.get_guild(self.guild_id)

    @property
    def cached_exempt_roles(self) -> list[Role]:
        """The cached version of the :attr:`exempt_roles`."""
        if self.guild is None:
            return []
        roles = filter(None, {self.guild.get_role(r) for r in self.exempt_roles})
        return list(roles)

    @property
    def cached_exempt_channels(self) -> list[Channel]:
        """The cached version of the :attr:`exempt_channels`."""
        if self.guild is None:
            return []
        channels = filter(None, {self.guild.get_channel(c) for c in self.exempt_channels})
        return list(channels)
