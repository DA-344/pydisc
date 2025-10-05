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

from .missing import MissingOr, MISSING
from .enums import ApplicationRoleConnectionMetadataType, Locale, try_enum

__all__ = ("ApplicationRoleConnectionMetadata",)


class ApplicationRoleConnectionMetadata:
    """Represents a role connection metadata.

    Parameters
    ----------
    type: :class:`ApplicationRoleConnectionMetadataType`
        The type of role metadata.
    key: :class:`str`
        The key of this metadata field. This must be within ``a-z``, ``0-9``, and ``_``, and up
        to 50 characters long.
    name: :class:`str`
        The name of this metadata field.
    description: :class:`str`
        The description of this metadata field.
    name_localizations: MissingOr[Dict[:class:`Locale`, :class:`str`]]
        A mapping of :class:`Locale` and :class:`str` that represent the available localizations for
        this role connection metadata name.
    description_localizations: MissingOr[Dict[:class:`Locale`, :class:`str`]]
        A mapping of :class:`Locale` and :class:`str` that represent the available localizations for
        this role connection metadata description.
    """

    def __init__(
        self,
        *,
        type: ApplicationRoleConnectionMetadataType,
        key: str,
        name: str,
        description: str,
        name_localizations: MissingOr[dict[Locale, str]] = MISSING,
        description_localizations: MissingOr[dict[Locale, str]] = MISSING,
    ) -> None:
        self.type: ApplicationRoleConnectionMetadataType = type
        """The type of role metadata."""
        self.key: str = key
        """The key of this metadata field."""
        self.name: str = name
        """The name of this metadata field."""
        self.description: str = description
        """The description of this metadata field."""
        self.name_localizations: MissingOr[dict[Locale, str]] = name_localizations
        """A mapping of :class:`Locale` and :class:`str` that represent the available localizations for
        this role connection metadata name.
        """
        self.description_localizations: MissingOr[dict[Locale, str]] = description_localizations
        """A mapping of :class:`Locale` and :class:`str` that represent the available localizations for
        this role connection metadata description.
        """

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApplicationRoleConnectionMetadata:
        return cls(
            type=try_enum(ApplicationRoleConnectionMetadataType, data["type"]),
            key=data["key"],
            name=data["name"],
            description=data["description"],
            name_localizations=data.get("name_localizations", MISSING),
            description_localizations=data.get("description_localizations", MISSING),
        )

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "type": self.type.value,
            "key": self.key,
            "name": self.name,
            "description": self.description,
        }
        if self.name_localizations is not MISSING:
            pd["name_localizations"] = {k.value: v for k, v in self.name_localizations.items()}
        if self.description_localizations is not MISSING:
            pd["description_localizations"] = {k.value: v for k, v in self.description_localizations.items()}
        return pd
