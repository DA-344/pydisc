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

from io import BytesIO
from typing import IO, TYPE_CHECKING, Literal

import yarl

from .file import File
from .missing import MISSING, MissingOr

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

AssetFormat = Literal["jpg", "jpeg", "webp", "png", "gif", "webm"]

__all__ = ("Asset",)


class AssetMixin:
    url: str
    _cache: CacheProtocol

    async def read(self) -> bytes:
        """Reads the bytes from the asset url.

        Returns
        -------
        :class:`bytes`
            The bytes from the asset.
        """

        client = self._cache.client
        session = self._cache.session

        async with session.get(
            self.url,
            proxy=client.proxy,
            proxy_auth=client.proxy_auth,
        ) as response:
            response.raise_for_status()
            return await response.read()

    async def save(
        self,
        fp: IO[bytes],
        *,
        seek: bool = True,
    ) -> int:
        """Writes the data of this asset into a buffer.

        This buffer can be any object that can be perfomed IO operations.

        Parameters
        ----------
        fp: IO[:class:`bytes`]
            The buffered object to save the data into.
        seek: :class:`bool`
            Whether to seek ``fp`` to ``0`` after writing.

        Returns
        -------
        :class:`int`
            The written bytes.
        """
        data = await self.read()
        written = fp.write(data)
        if seek:
            fp.seek(0)
        return written

    async def to_file(
        self,
        *,
        filename: MissingOr[str] = MISSING,
        description: MissingOr[str] = MISSING,
        spoiler: MissingOr[bool] = MISSING,
    ) -> File:
        """Converts this asset into a :class:`File` object.

        Parameters
        ----------
        filename: MissingOr[:class:`str`]
            The filename to set to the returned file object.
        description: MissingOr[:class:`str`]
            The description to set to the returned file object.
        spoiler: MissingOr[:class:`bool`]
            Whether to mark the returned file object as spoiler.

        Returns
        -------
        :class:`File`
            The converted file.
        """
        buffer = BytesIO(await self.read())
        if filename is MISSING:
            filename = yarl.URL(self.url).name
        return File(
            buffer,
            filename=filename,
            description=description or None,
            spoiler=spoiler,
        )


class Asset(AssetMixin):
    """Represents a Discord CDN asset."""

    CDN_URL = "https://cdn.discordapp.com/"
    MEDIA_URL = "https://media.discordapp.net/"

    def __init__(
        self,
        *,
        route: str,
        key: str,
        animated: bool,
        cache: CacheProtocol,
        format: AssetFormat,
        use_media: bool = False,
    ) -> None:
        self.route: str = route
        """The route this asset points to."""
        self.key: str = key
        """The asset key."""
        self.animated: bool = animated
        """Whether this asset is animated."""
        self._cache: CacheProtocol = cache
        self.format: AssetFormat = format
        """The extension format type of this asset."""
        self._base_url: str = self.CDN_URL if use_media is False else self.MEDIA_URL

    @property
    def url(self) -> str:
        """Returns this asset full url."""
        return self._base_url + self.route
