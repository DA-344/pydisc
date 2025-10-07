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
from typing import IO, TYPE_CHECKING, Any

import yarl

from . import utils
from .asset import AssetMixin
from .file import File
from .flags import AttachmentFlags
from .missing import MISSING, MissingOr
from .mixins import Hashable

if TYPE_CHECKING:
    from .cache._types import CacheProtocol

__all__ = ("Attachment",)


class Attachment(AssetMixin, Hashable):
    """Represents an attachment from Discord."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The ID of this attachment."""
        self.size: int = data["size"]
        """This attachment's size in bytes."""
        self.height: int | None = data.get("height")
        """The height of this attachment in pixels, if applicable."""
        self.width: int | None = data.get("width")
        """The width of this attachment in pixels, if applicable."""
        self.filename: str = data["filename"]
        """The name of the file attached."""
        self.title: str | None = data.get("title")
        """The title of the file attached."""
        self.description: str | None = data.get("description")
        """The description of the file attached."""
        self.url: str = data["url"]
        """The URL of this attachment."""
        self.proxy_url: str = data["proxy_url"]
        """A proxied URL of this attachment."""
        self.ephemeral: bool = data.get("ephemeral", False)
        """Whether this attachment is ephemeral."""
        self.duration: float | None = data.get("duration_secs")
        """The duration of this attachment's audio, if applicable."""
        self.waveform: bytes | None = None
        """The waveform of this attacment's audio, if applicable."""
        self.content_type: str | None = data.get("content_type")
        """The content type of this attachment."""

        if wf := data.get("waveform"):
            self.waveform = utils.base64_to_bytes(wf)

        self._flags: int = data.get("flags", 0)

    @property
    def flags(self) -> AttachmentFlags:
        """The flags of this attachment."""
        return AttachmentFlags(self._flags)

    def is_spoiler(self) -> bool:
        """Whether this attachment is an spoiler."""
        return AttachmentFlags.spoiler in self.flags or self.filename.startswith("SPOILER_")

    def is_voice_message(self) -> bool:
        """Whether the current attachment is a voice message."""
        return self.waveform is not None and self.duration is not None

    async def read(self, *, use_proxied: bool = False) -> bytes:
        """Reads the bytes from the attachment url.

        Using the ``use_proxied`` parameter may allow to receiving the attachment's bytes
        after a short period of the parent message being deleted. Basically, uses :attr:`proxy_url`
        instead of :attr:`url`.

        Returns
        -------
        :class:`bytes`
            The bytes from the attachment.
        """
        if use_proxied:
            client = self._cache.client
            session = self._cache.session
            async with session.get(
                self.proxy_url,
                proxy=client.proxy,
                proxy_auth=client.proxy_auth,
            ) as response:
                response.raise_for_status()
                return await response.read()
        return await super().read()

    async def save(self, fp: IO[bytes], *, seek: bool = True, use_proxied: bool = False) -> int:
        """Writes the data of this asset into a buffer.

        This buffer can be any object that can be perfomed IO operations.

        Parameters
        ----------
        fp: IO[:class:`bytes`]
            The buffered object to save the data into.
        seek: :class:`bool`
            Whether to seek ``fp`` to ``0`` after writing.
        use_proxied: :class:`bool`
            Using this parameter may allow to receiving the attachment's bytes
            after a short period of the parent message being deleted. Basically, uses :attr:`proxy_url`
            instead of :attr:`url`.

        Returns
        -------
        :class:`int`
            The written bytes.
        """
        if use_proxied:
            data = await self.read(use_proxied=True)
            written = fp.write(data)
            if seek:
                fp.seek(0)
            return written
        return await super().save(fp, seek=seek)

    async def to_file(
        self,
        *,
        filename: MissingOr[str] = MISSING,
        description: MissingOr[str] = MISSING,
        spoiler: MissingOr[bool] = MISSING,
        use_proxied: bool = False,
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
        use_proxied: :class:`bool`
            Using this parameter may allow to receiving the attachment's bytes
            after a short period of the parent message being deleted. Basically, uses :attr:`proxy_url`
            instead of :attr:`url`.

        Returns
        -------
        :class:`File`
            The converted file.
        """
        buffer = BytesIO(await self.read(use_proxied=use_proxied))
        if filename is MISSING:
            filename = yarl.URL(self.url).name
        return File(
            buffer,
            filename=filename,
            description=description or None,
            spoiler=spoiler,
        )

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "filename": self.filename,
            "id": self.id,
            "proxy_url": self.proxy_url,
            "size": self.size,
            "url": self.url,
            "spoiler": self.is_spoiler(),
        }
        if self.height:
            pd["height"] = self.height
        if self.width:
            pd["width"] = self.width
        if self.content_type:
            pd["content_type"] = self.content_type
        if self.description is not None:
            pd["description"] = self.description
        return pd

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None, cache: CacheProtocol) -> list[Attachment]:
        if not data:
            return []
        return [Attachment(d, cache) for d in data]
