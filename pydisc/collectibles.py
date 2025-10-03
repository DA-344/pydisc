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
from .enums import NameplatePalette, try_enum

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = (
    "Collectibles",
    "Nameplate",
)


class Collectibles:
    """Represents a user's collectibles available at :attr:`abc.User.collectibles`."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.nameplate: Nameplate | None = Nameplate.from_dict(data.get("nameplate"), cache)
        """The nameplate of this user."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Collectibles | None:
        if data is None:
            return None
        return Collectibles(data, cache)


class Nameplate:
    """Represents a user's nameplate."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.sku_id: int = int(data["sku_id"])
        """The SKU ID of the nameplate."""
        self._asset: str = data["asset"]
        self._cache: CacheProtocol = cache
        self.label: str = data["labek"]
        """The nameplate label."""
        self.palette: NameplatePalette = try_enum(NameplatePalette, data["palette"])
        """The background color of the nameplate."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Nameplate | None:
        if data is None:
            return None
        return Nameplate(data, cache)

    @property
    def static(self) -> Asset:
        """The static asset of this nameplate."""
        return Asset(
            route=f"assets/collectibles/{self._asset}static.png",
            key=self._asset,
            animated=False,
            cache=self._cache,
            format="png",
        )

    @property
    def animated(self) -> Asset:
        """The animated asset of this nameplate."""
        return Asset(
            route=f"assets/collectibles/{self._asset}asset.webm",
            key=self._asset,
            animated=True,
            cache=self._cache,
            format="webm",
        )
