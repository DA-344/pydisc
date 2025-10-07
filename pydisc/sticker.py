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

from typing import TYPE_CHECKING, Any, Self

from .asset import Asset
from .enums import StickerFormatType, StickerType, try_enum
from .mixins import Hashable
from .user import User
from .utils import _get_snowflake

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .guild import Guild


class StickerPack(Hashable):
    """Represents a sticker pack for standard stickers."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the sticker pack."""
        self.stickers: list[Sticker] = Sticker.from_dict_array(data["stickers"], cache)
        """The stickers in the pack."""
        self.name: str = data["name"]
        """The name of the packet."""
        self.sku_id: int = int(data["sku_id"])
        """The ID of the pack's SKU."""
        self.cover_sticker_id: int | None = _get_snowflake("cover_sticker_id", data)
        """The ID of the sticker shown as the pack icon."""
        self.description: str = data["description"]
        """The description of this pack."""
        self._banner: int | None = _get_snowflake("banner_asset_id", data)
        self._cache: CacheProtocol = cache

    @property
    def banner(self) -> Asset | None:
        """The banner of this pack, or ``None``."""
        if self._banner is None:
            return None
        return Asset(
            route=f"app-assets/710982414301790216/store/{self._banner}.png",
            key=str(self._banner),
            animated=False,
            cache=self._cache,
            format="png",
        )


class StickerItem(Hashable):
    """Represents a sticker item received in a message."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the sticker."""
        self.name: str = data["name"]
        """The name of this sticker."""
        self.format: StickerFormatType = try_enum(StickerFormatType, data["format_type"])
        """The sticker's image format."""
        self._cache: CacheProtocol = cache

    @property
    def cached(self) -> Sticker | None:
        """Returns the cached version of this sticker."""
        return self._cache.get_sticker(self.id)

    async def fetch(self) -> Sticker:
        """Fetches this sticker item.

        You should not call this if :meth:`is_item` is ``False``.
        """

        client = self._cache.client
        http = client.http
        data = await http.get_sticker(self.id)
        sticker = Sticker(data, self._cache)
        self._cache.store_sticker(sticker)
        return sticker

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None, cache: CacheProtocol) -> list[Self]:
        if not data:
            return []
        return [cls(d, cache) for d in data]


class Sticker(StickerItem):
    """Represents a sticker object that can be attached to a message."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)
        self.pack_id: int | None = _get_snowflake("pack_id", data)
        """The ID of the pack this sticker belongs to. Only applicable if :meth:`is_standard`
        is ``True``.
        """
        self.description: str | None = data.get("description")
        """The description of this stacked."""
        self.tags: list[str] = [t.strip() for t in data.get("tags", "").split(",")]
        """A list of tags for autocomplete/suggestions of this sticker."""
        self.type: StickerType = try_enum(StickerType, data["type"])
        """This sticker's type."""
        self.available: bool = data.get("available", False)
        """Whether this sticker can be used. May be ``False`` if the parent guild has lost Server Boosts."""
        self.guild_id: int | None = _get_snowflake("guild_id", data)
        """The guild ID this sticker is from."""

        user: dict[str, Any] | None = data.get("user")
        self.user: User | None = cache.get_user(_get_snowflake("id", user or {}))
        """The user that created this sticker."""
        if self.user is None:
            self.user = User.from_dict(user, cache)
            if self.user:
                cache.store_user(self.user)
        else:
            if user:
                self.user._update(user)

        self.sort_value: int | None = data.get("sort_value")
        """The stickers sort order within its packet. Only applicable if :meth:`is_standard`
        is ``True``.
        """

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Sticker | None:
        if data is None:
            return None
        return Sticker(data, cache)

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None, cache: CacheProtocol) -> list[Sticker]:
        if not data:
            return []
        return [Sticker(s, cache) for s in data]

    def is_standard(self) -> bool:
        """Whether this sticker is part of an standard pack."""
        return self.type is StickerType.standard

    @property
    def guild(self) -> Guild | None:
        """The guild this sticker is from, if applicable."""
        return self._cache.get_guild(self.guild_id)

    async def fetch_pack(self) -> StickerPack:
        """Fetches this sticker's pack."""

        if self.pack_id is None:
            raise RuntimeError("there is no pack for this sticker")

        http = self._cache.http
        data = await http.get_sticker_pack(self.pack_id)
        return StickerPack(data, self._cache)
