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

from pydisc.abc import Mentionable
from pydisc.enums import CommandPermissionOverwriteType, CommandType, EntryPointHandlerType, Locale, try_enum
from pydisc.flags import Permissions
from pydisc.mixins import Hashable
from pydisc.utils import _get_snowflake

from .options import Option

if TYPE_CHECKING:
    from pydisc.abc import Channel, User
    from pydisc.cache._types import CacheProtocol
    from pydisc.guild import Guild
    from pydisc.role import Role


class ApplicationCommand(Hashable, Mentionable):
    """Represents an application command received from the Discord API."""

    type: CommandType
    """This application command's type."""
    application_id: int
    """The application ID this command is bound to."""
    guild_id: int | None
    """The specific guild ID in which this command is restricted to."""
    name: str
    """The command name."""
    description: str
    """The command description"""
    default_member_permissions: Permissions | None
    """The set of permissions required for a user to use this command. This can be changed by server administrators."""
    nsfw: bool
    """Whether this command is marked as NSFW, and thus only available on NSFW-flagged channels."""
    version: int
    """An autoincrementing version identifier updated during substantial record changes."""
    handler_type: EntryPointHandlerType | None
    """The handler type of this command. This is only applicable when :attr:`type` is :attr:`CommandType.primary_entry_point`."""
    options: list[Option]
    """This command's options. This is only applicable when :attr:`type` is :attr:`CommandType.chat_input`."""
    name_localizations: dict[Locale, str]
    """A mapping of :class:`Locale` and :class:`str` that represent the available localizations of this command's name."""
    description_localizations: dict[Locale, str]
    """A mapping of :class:`Locale` and :class:`str` that represent the available localizations of this command's description."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        self._cache: CacheProtocol = cache
        self._update(data, cache)

    def _get_mention_string(self) -> str:
        return f"</{self.name}:" + "{id}>"

    def _update(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.type: CommandType = try_enum(CommandType, data.get("type", 1))
        self.application_id: int = int(data["application_id"])
        self.guild_id: int | None = _get_snowflake("guild_id", data)
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.default_member_permissions: Permissions | None = (
            Permissions(int(data["default_member_permissions"]))
            if data.get("default_member_permissions") is not None
            else None
        )
        self.nsfw: bool = data.get("nsfw", False)
        self.version: int = int(data["version"])
        self.handler_type: EntryPointHandlerType | None = (
            try_enum(EntryPointHandlerType, data["handler"]) if data.get("handler") is not None else None
        )
        self.options: list[Option] = Option.from_dict_array(data.get("options"))
        self.name_localizations: dict[Locale, str] = dict(
            map(
                lambda i: (try_enum(Locale, i[0]), i[1]),
                data.get("name_localizations", {}).items(),
            ),
        )
        self.description_localizations: dict[Locale, str] = dict(
            map(
                lambda i: (try_enum(Locale, i[0]), i[1]),
                data.get("description_localizations", {}).items(),
            ),
        )

    @property
    def guild(self) -> Guild | None:
        """Returns the cached version of :attr:`.guild_id`"""
        return self._cache.get_guild(self.guild_id)

    def get_local(self) -> Command | None:
        """Returns the local command version of this API fetched one.

        With a local command, you can invoke the callback with it and use the
        local parameters instead of the API sent ones, in case any got renamed,
        or added options later on.
        """
        return self._cache.get_command(self.name)


class ApplicationCommandPermissionOverwrite(Hashable):
    """Represents an application command permission overwrite for an object."""

    def __init__(self, data: dict[str, Any], guild_id: int, cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the role, user, or channel this overwrite belongs it.

        This may also be the guild ID if the object is the ``@everyone`` role, or
        the guild ID - 1 if this is for all the channels in the guild.

        You may check this with the :meth:`is_default_role` and :meth:`is_all_channels`
        helper methods.
        """
        self.type: CommandPermissionOverwriteType = try_enum(
            CommandPermissionOverwriteType,
            data["type"],
        )
        """The type of this overwrite."""
        self.permission: bool = data["permission"]
        """Whether this object is allowed to use the command."""
        self._guild: int = guild_id
        self._cache: CacheProtocol = cache

    def is_default_role(self) -> bool:
        """Whether this overwrite is for the ``@everyone`` role in the guild."""
        return self.id == self._guild

    def is_all_channels(self) -> bool:
        """Whether this overwrite is for All Channels in the guild."""
        return self.id == (self._guild - 1)

    @property
    def cached_object(self) -> User | Role | Channel | None:
        """Returns the cached object of this overwrite.

        This may return ``None`` if :meth:`is_all_channels` is ``True``.
        """
        # NOTE: maybe create a sentinel for AllChannels?
        if self.is_all_channels():
            return None

        guild = self._cache.get_guild(self._guild)
        methods = {
            CommandPermissionOverwriteType.user: self._cache.get_user,
            CommandPermissionOverwriteType.role: guild.get_role if guild is not None else (lambda i: None),
            CommandPermissionOverwriteType.channel: guild.get_channel if guild is not None else (lambda i: None),
        }
        return methods[self.type](self.id)

    @classmethod
    def from_dict_array(
        cls, data: list[dict[str, Any]], cache: CacheProtocol, guild: int
    ) -> list[ApplicationCommandPermissionOverwrite]:
        return [ApplicationCommandPermissionOverwrite(d, guild, cache) for d in data]


class ApplicationCommandPermissions(Hashable):
    """Represents the permissions fetched from an application command."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the command. If this is the same as :attr:`application_id` then this is a global
        permissions object and does not have any explicit overwrites.
        """
        self.application_id: int = int(data["application_id"])
        """The application ID owner of this command."""
        self.guild_id: int = int(data["guild_id"])
        """The guild ID this permissions belong to."""
        self.permissions: list[ApplicationCommandPermissionOverwrite] = (
            ApplicationCommandPermissionOverwrite.from_dict_array(
                data["permissions"],
                cache,
                self.guild_id,
            )
        )
        """The permission overwrites for this command in this guild."""

    def is_global(self) -> bool:
        """Whether this permissions are applied to all the commands of the application in the guild,
        or just overridden for this command.
        """
        return self.id == self.application_id
