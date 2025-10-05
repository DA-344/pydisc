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
from .enums import TeamMemberRole, TeamMembershipState, try_enum
from .user import User, PartialUser
from .mixins import Hashable

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "Team",
    "TeamMember",
)


class Team(Hashable):
    """Represents a Team."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._icon: str | None = data.get("icon")
        self.id: int = int(data["id"])
        """The team ID."""
        self.name: str = data["name"]
        """The name of this team."""
        self.owner_id: int = int(data["owner_user_id"])
        """The user ID of the owner of the team."""
        self._cache: CacheProtocol = cache
        self.members: list[TeamMember] = TeamMember.from_dict_array(data["members"], cache, self)
        """The members of the team."""

    @property
    def owner(self) -> User | None:
        """Returns the cached owner."""
        return self._cache.get_user(self.owner_id)

    @property
    def icon(self) -> Asset | None:
        """Returns the team icon."""
        if self._icon is None:
            return None
        return Asset(
            route=f"team-icons/{self.id}/{self._icon}.png",
            key=self._icon,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Team | None:
        if data is None:
            return None
        return Team(data, cache)


class TeamMember:
    """Represents a member from a team."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, parent: Team) -> None:
        self.membership_state: TeamMembershipState = try_enum(TeamMembershipState, data["membership_state"])
        """The user's invitation state on the team."""
        self.team_id: int = int(data["team_id"])
        """The ID of the team this member is part of."""

        user: dict[str, Any] = data["user"]
        self.user: PartialUser = PartialUser(user, cache)
        """The partial user this team member represents."""
        if cached_user := cache.get_user(self.user.id):
            self.user = cached_user
            self.user.__init__(user, cache)

        self.role: TeamMemberRole
        """The role of this member in the team."""

        if parent.owner_id == self.user.id:
            self.role = TeamMemberRole.owner
        else:
            self.role = try_enum(TeamMemberRole, data["role"])

    @classmethod
    def from_dict_array(cls, array: list[dict[str, Any]], cache: CacheProtocol, parent: Team) -> list[TeamMember]:
        if not array:
            return []
        return [TeamMember(data, cache, parent) for data in array]
