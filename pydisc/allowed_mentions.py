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
from typing import Any

from .abc import Snowflake
from .missing import MissingOr, MISSING

__all__ = (
    "AllowedMentions",
)


class AllowedMentions:
    """Represents the mentions parsed/to-parse in a :class:`Message`."""

    def __init__(
        self,
        *,
        everyone: MissingOr[bool] = MISSING,
        users: MissingOr[bool | Sequence[Snowflake]] = MISSING,
        roles: MissingOr[bool | Sequence[Snowflake]] = MISSING,
        replied_user: MissingOr[bool] = MISSING,
    ) -> None:
        self._everyone: MissingOr[bool] = everyone or MISSING
        self._users: MissingOr[bool] = bool(users) or MISSING
        self._user_ids: MissingOr[Sequence[Snowflake]] = users if isinstance(users, Sequence) else MISSING
        self._roles: MissingOr[bool] = bool(roles) or MISSING
        self._role_ids: MissingOr[Sequence[Snowflake]] = roles if isinstance(roles, Sequence) else MISSING
        self._replied_user: MissingOr[bool] = replied_user or MISSING

    @property
    def everyone(self) -> bool:
        """Whether everyone mentions are parsed."""
        return bool(self._everyone)

    @everyone.setter
    def everyone(self, value: bool | None) -> None:
        self._everyone = bool(value) or MISSING

    @property
    def users(self) -> bool | Sequence[Snowflake]:
        r"""A bool denoting whether user mentions are parsed, or a sequence of
        :class:`abc.Snowflake`\s that represent the mentions users IDs that will be
        parsed.
        """
        if self._user_ids is not MISSING:
            return self._user_ids
        return bool(self._users)

    @users.setter
    def users(self, value: bool | Sequence[Snowflake] | None) -> None:
        if value in (None, False):
            self._users = MISSING
            self._user_ids = MISSING
        elif value is True:
            self._users = True
            self._user_ids = MISSING
        elif isinstance(value, Sequence):
            self._users = MISSING
            self._user_ids = value

    @property
    def roles(self) -> bool | Sequence[Snowflake]:
        r"""A bool denoting whether role mentions are parsed, or a sequence of
        :class:`abc.Snowflake`\s that represent the mentions roles IDs that will be
        parsed.
        """
        if self._user_ids is not MISSING:
            return self._user_ids
        return bool(self._users)

    @roles.setter
    def roles(self, value: bool | Sequence[Snowflake] | None) -> None:
        if value in (None, False):
            self._roles = MISSING
            self._role_ids = MISSING
        elif value is True:
            self._roles = True
            self._role_ids = MISSING
        elif isinstance(value, Sequence):
            self._roles = MISSING
            self._role_ids = value

    @property
    def replied_user(self) -> bool:
        """Whether the message author of the replied message is parsed."""
        return bool(self._replied_user)

    @replied_user.setter
    def replied_user(self, value: bool | None) -> None:
        self._replied_user = bool(value) or MISSING

    @classmethod
    def all(cls) -> AllowedMentions:
        """Creates an AllowedMentions instance with every flag set to True."""
        return AllowedMentions(
            everyone=True,
            users=True,
            roles=True,
            replied_user=True,
        )

    @classmethod
    def none(cls) -> AllowedMentions:
        """Creates an AllowedMentions instance with every flag set to False."""
        return AllowedMentions()

    def to_dict(self) -> dict[str, Any]:
        parse: list[str] = []
        pd: dict[str, Any] = {}

        if self._everyone:
            parse.append("everyone")
        if self._users:
            parse.append("users")
        if self._user_ids:
            pd["users"] = [str(u.id) for u in self._user_ids]
        if self._roles:
            parse.append("roles")
        if self._role_ids:
            pd["roles"] = [str(r.id) for r in self._role_ids]
        if self._replied_user:
            pd["replied_user"] = True

        pd["parse"] = parse
        return pd

    def merge(self, other: AllowedMentions) -> AllowedMentions:
        """Merges two AllowedMentions instances to combine them into one
        that has all the enabled flags from the both.
        """

        everyone = other.everyone or self.everyone
        users = other.users or self.users
        roles = other.roles or self.roles
        replied_user = other.replied_user or self.replied_user
        return AllowedMentions(
            everyone=everyone,
            users=users,
            roles=roles,
            replied_user=replied_user,
        )
