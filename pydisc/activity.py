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
from .flags import ActivityFlags
from .enums import ActivityStatusDisplayType, ActivityType, try_enum
from .emoji import Emoji
from .utils import _get_snowflake

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "ActivityTimestamps",
    "ActivityButton",
    "ActivityParty",
    "ActivityAssets",
    "ActivitySecrets",
    "Activity",
)


class ActivityTimestamps:
    """Represents an activity's timestamps."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.start: datetime.datetime | None = None
        """When the activity started."""
        self.end: datetime.datetime | None = None
        """When the activity ends."""

        for key in ("start", "end"):
            try:
                value = data[key]
            except KeyError:
                pass
            else:
                setattr(self, key, datetime.datetime.fromtimestamp(value, datetime.timezone.utc))

    @classmethod
    def from_data(cls, data: dict[str, Any] | None) -> ActivityTimestamps | None:
        if data is None:
            return None
        return ActivityTimestamps(data)


class ActivityButton:
    """Represents a button from an activity.

    .. warning::

        This is **not the same** as an interactible component
        :class:`Button` object.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.label: str = data["label"]
        """The label of this button."""
        self.url: str = data["url"]
        """The URL of this of this button."""

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None) -> list[ActivityButton]:
        if not data:
            return []
        return [ActivityButton(d) for d in data]


class ActivityParty:
    """Represents a party for an activity."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.id: str | None = data.get("id")
        """The ID of this party. This is not an integer."""
        self._sizes: tuple[int, int] | tuple[()] = tuple(data.get("size", []))

    @property
    def current_size(self) -> int | None:
        """The current size of this party."""
        try:
            return self._sizes[0]  # pyright: ignore[reportGeneralTypeIssues]
        except IndexError:
            return None

    @property
    def max_size(self) -> int | None:
        """The maximum size of this party."""
        try:
            return self._sizes[1]  # pyright: ignore[reportGeneralTypeIssues]
        except IndexError:
            return None

    @classmethod
    def from_data(cls, data: dict[str, Any] | None) -> ActivityParty | None:
        if data is None:
            return None
        return ActivityParty(data)


class ActivityAssets:
    """Represents the assets of an activity."""

    def __init__(self, data: dict[str, Any], parent: Activity, cache: CacheProtocol) -> None:
        self._parent: Activity = parent
        self._cache: CacheProtocol = cache
        self._large_image: str | None = data.get("large_image")
        self._small_image: str | None = data.get("small_image")
        self.large_text: str | None = data.get("large_text")
        """The text displayed when hovering on the large image of the activity."""
        self.large_url: str | None = data.get("large_url")
        """The URL set to the large image of the activity."""
        self.small_text: str | None = data.get("small_text")
        """The text displayed when hovering on the small image of the activity."""
        self.small_url: str | None = data.get("small_url")
        """The URL set to the small image of the activity."""

    @property
    def large_image(self) -> Asset | None:
        """The large image asset."""
        if self._large_image is None:
            return None
        return self._image_asset(self._large_image)

    @property
    def small_image(self) -> Asset | None:
        """The small image asset."""
        if self._small_image is None:
            return None
        return self._image_asset(self._small_image)

    def _image_asset(self, key: str) -> Asset | None:
        if key.startswith("mp:"):
            return Asset(
                route=key.removeprefix("mp:"),
                key=key,
                animated=False,
                cache=self._cache,
                format="png",
                use_media=True,
            )
        return Asset(
            route=f"app-assets/{self._parent.application_id}/{key}.png",
            key=key,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @classmethod
    def from_data(cls, data: dict[str, Any] | None, parent: Activity, cache: CacheProtocol) -> ActivityAssets | None:
        if data is None:
            return None
        return ActivityAssets(data, parent, cache)


class ActivitySecrets:
    """The secrets of an activity rich presence."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.join: str | None = data.get("join")
        """The secret for joining the party."""
        self.spectate: str | None = data.get("spectate")
        """The secret for spectating a game."""
        self.match: str | None = data.get("match")
        """The secret for an instanced match."""

    @classmethod
    def from_data(cls, data: dict[str, Any] | None) -> ActivitySecrets | None:
        if data is None:
            return None
        return ActivitySecrets(data)


class Activity:
    """Represents an activity."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol | None) -> None:
        self.name: str = data["name"]
        """The name of this activity."""
        self.type: ActivityType = try_enum(ActivityType, data["type"])
        """The type of this activity."""

        self.url: str | None = data.get("url")
        """The URL of this activity. This usually points to the stream when :attr:`type` is :attr:`ActivityType.streaming`."""
        self.created_at: datetime.datetime = datetime.datetime.fromtimestamp(data["created_at"], datetime.timezone.utc)
        """The timestamp on which this activity was added to the user's session."""
        self.timestamps: ActivityTimestamps | None = ActivityTimestamps.from_data(data.get("timestamps"))
        """The start and end timestamps of this activity."""
        self.application_id: int | None = _get_snowflake("application_id", data)
        """The application ID of the game."""

        self.status_display_type: ActivityStatusDisplayType | None = None
        """How this activity is displayed in the user's profile."""
        if sdt := data.get("status_display_type"):
            self.status_display_type = try_enum(ActivityStatusDisplayType, sdt)
        self.details: str | None = data.get("details")
        """What the player is currently doing."""
        self.details_url: str | None = data.get("details_url")
        """The URL set to the details button."""
        self.state: str | None = data.get("state")
        """The state of the current user party, or the text used for the status when :attr:`type` is :attr:`ActivityType.custom`."""
        self.state_url: str | None = data.get("state_url")
        """The URL of the state button."""

        self.emoji: Emoji | None = None
        """The emoji of this activity. Only when :attr:`type` is :attr:`ActivityType.custom`."""
        if emoji := data.get("emoji"):
            if cache is not None:
                self.emoji = Emoji.from_dict(emoji, cache)

        self.party: ActivityParty | None = ActivityParty.from_data(data.get("party"))
        """The activity's party."""

        self.assets: ActivityAssets | None = None
        """The activity's assets."""
        if cache is not None:
            self.assets = ActivityAssets.from_data(data.get("assets"), self, cache)

        self.secrets: ActivitySecrets | None = ActivitySecrets.from_data(data.get("secrets"))
        """The secrets of the rich presence joining and spectating."""
        self.instance: bool = data.get("instance", False)
        """Whether this activity is an instanced game session."""
        self._flags: int = data.get("flags", 0)
        self.buttons: list[ActivityButton] = ActivityButton.from_dict_array(data.get("buttons"))
        """The buttons of this activity."""

    @property
    def flags(self) -> ActivityFlags:
        """The flags of this activity."""
        return ActivityFlags(self._flags)

    @classmethod
    def create_custom(cls, *, name: str, state: str) -> Activity:
        """Creates a custom activity for setting it to a presence."""
        return Activity({"name": name, "type": ActivityType.custom.value, "state": state}, None)

    @classmethod
    def create_watching(cls, *, name: str) -> Activity:
        """Creates a "Watching <name>" activity."""
        return Activity({"name": name, "type": ActivityType.watching.value}, None)

    @classmethod
    def create_listening(cls, *, name: str) -> Activity:
        """Creates a "Listening to <name>" activity."""
        return Activity({"name": name, "type": ActivityType.listening.value}, None)

    @classmethod
    def create_streaming(cls, *, name: str, details: str, url: str) -> Activity:
        """Creates a "Streaming <details>" activity."""
        return Activity({"name": name, "type": ActivityType.streaming.value, "details": details, "url": url}, None)

    @classmethod
    def create_playing(cls, *, name: str) -> Activity:
        """Creates a "Playing <name>" activity."""
        return Activity({"name": name, "type": ActivityType.playing.value}, None)

    def to_dict(self) -> dict[str, Any]:
        # to dict is technically only for the types we can set so i'll just return
        # the one needed per type

        base = {
            "name": self.name,
            "type": self.type.value,
        }

        if self.type is ActivityType.streaming:
            assert self.url
            assert self.details

            base["url"] = self.url
            base["details"] = self.details
        elif self.type is ActivityType.custom:
            assert self.state

            base["state"] = self.state
        return base
