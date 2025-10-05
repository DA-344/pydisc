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
from typing import Any

from .flags import Permissions
from .enums import PermissionOverwriteType, try_enum
from .utils import get

__all__ = ("PermissionOverwrite",)


class PermissionOverwrite:
    """Represents a permission overwrite for an object."""

    def __init__(
        self,
        *,
        id: int,
        type: PermissionOverwriteType,
        allow: Permissions,
        deny: Permissions,
    ) -> None:
        self.id: int = id
        self.type: PermissionOverwriteType = type
        self.allow: Permissions = allow
        self.deny: Permissions = deny

    @classmethod
    def from_member(cls, id: int, *, allow: Permissions, deny: Permissions) -> PermissionOverwrite:
        """Creates a PermissionOverwrite object passing ``type`` as :attr:`PermissionOverwriteType.member`
        by default.
        """
        return PermissionOverwrite(
            id=id,
            type=PermissionOverwriteType.member,
            allow=allow,
            deny=deny,
        )

    @classmethod
    def from_role(cls, id: int, *, allow: Permissions, deny: Permissions) -> PermissionOverwrite:
        """Creates a PermissionOverwrite object passing ``type`` as :attr:`PermissionOverwriteType.role`
        by default.
        """
        return PermissionOverwrite(
            id=id,
            type=PermissionOverwriteType.role,
            allow=allow,
            deny=deny,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "allow": str(self.allow.value),
            "deny": str(self.deny.value),
        }

    def is_role(self) -> bool:
        """Whether this overwrite is for a role."""
        return self.type is PermissionOverwriteType.role

    def is_member(self) -> bool:
        """Whether this overwrite is for a member."""
        return self.type is PermissionOverwriteType.member

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PermissionOverwrite:
        id = int(data["id"])
        type = try_enum(PermissionOverwriteType, data["type"])
        allow = Permissions(int(data["allow"]))
        deny = Permissions(int(data["deny"]))
        return PermissionOverwrite(
            id=id,
            type=type,
            allow=allow,
            deny=deny,
        )

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]], guild_id: int) -> list[PermissionOverwrite]:
        if not data:
            return []
        ows = [PermissionOverwrite.from_dict(ow) for ow in data]
        everyone = get(ows, id=guild_id)
        if everyone is not None:
            idx = ows.index(everyone)
            ows.pop(idx)
            ows.insert(0, everyone)
        return ows
