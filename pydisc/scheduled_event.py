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

from .enums import ScheduledEventEntityType, ScheduledEventPrivacyLevel, ScheduledEventStatus, try_enum
from .mixins import Hashable
from .utils import _get_snowflake, parse_time
from .user import User

if TYPE_CHECKING:
    from .cache._types import CacheProtocol


class ScheduledEvent(Hashable):
    """Represents a :class:`Guild` scheduled event."""

    id: int
    """The ID of this event."""
    guild_id: int
    """The guild ID this event belongs to."""
    channel_id: int | None
    """The channel ID the event will be hosted in, or ``None`` if :attr:`entity_type` is
    :attr:`ScheduledEventEntityType.external`.
    """
    creator_id: int | None
    """The user ID that created the event. This will be ``None`` for events created before
    the October 25th, 2021.
    """
    name: str
    """The name of this event."""
    description: str | None
    """The description of this event."""
    start_time: datetime.datetime
    """When this event will start."""
    end_time: datetime.datetime | None
    """When this event will end. This will never be ``None`` if :attr:`entity_type` is
    :attr:`ScheduledEventEntityType.external`.
    """
    privacy_level: ScheduledEventPrivacyLevel
    """The privacy level of this scheduled event."""
    status: ScheduledEventStatus
    """The status of this event."""
    entity_type: ScheduledEventEntityType
    """The entity type of this event."""
    entity_id: int | None
    """The ID of the entity associated with this event."""
    entity_metadata: ScheduledEventEntityMetadata | None
    """The entity metadata of this event."""
    creator: User | None
    """The user that created the event. This will be ``None`` for events created before
    the October 25th, 2021.
    """
    user_count: int | None
    """The number of users subscribed to this event."""
    _image: str | None
    recurrence_rule: ScheduledEventRecurrenceRule | None
    """The recurrence rule of this event."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self._update(data)

    def _update(self, data: dict[str, Any]) -> None:
        self.id = int(data["id"])
        self.guild_id = int(data["guild_id"])
        self.channel_id = _get_snowflake("channel_id", data)
        self.creator_id = _get_snowflake("creator_id", data)
        self.name = data["name"]
        self.description = data.get("description")
        self.start_time = parse_time(data["scheduled_start_time"])
        self.end_time = parse_time(data.get("scheduled_end_time"))
        self.privacy_level = try_enum(ScheduledEventPrivacyLevel, data["privacy_level"])
        self.status = try_enum(ScheduledEventStatus, data["status"])
        self.entity_type = try_enum(ScheduledEventEntityType, data["entity_type"])
        self.entity_id = _get_snowflake("entity_id", data)
        self.entity_metadata = ScheduledEventEntityMetadata.from_dict(data.get("entity_metadata"))
    
        user = data.get("user")
        user_id = _get_snowflake("id", user or {})

        if self.creator_id is None:
            self.creator = self._cache.get_user(user_id)
            if self.creator is not None and user is not None:
                self.creator._update(user)
            elif self.creator is None and user is not None:
                self.creator = User(user, self._cache)
                self._cache.store_user(user)
        else:
            self.creator = self._cache.get_user(self.creator_id)
            if user is not None and self.creator is not None:
                self.creator._update(user)

        self.user_count = data.get("user_count")
        self._image = data.get("image")
        self.recurrence_rule = ScheduledEventRecurrenceRule.from_dict(data.get("recurrence_rule"))


class ScheduledEventEntityMetadata:
    """Represents the entity metadata for a scheduled event."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.location: str | None = data.get("location")
        """The location of the event."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ScheduledEventEntityMetadata | None:
        if data is None:
            return None
        return ScheduledEventEntityMetadata(data)


class ScheduledEventRecurrenceRule:
    """Represents the recurrence rule for a scheduled event."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ScheduledEventRecurrenceRule | None:
        if data is None:
            return None
