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

import io
import os
from typing import IO, Any

from .flags import AttachmentFlags
from .missing import MISSING, MissingOr

__all__ = ("File",)


class File:
    """Represents a file you can send with a message."""

    def __init__(
        self,
        fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase,
        filename: MissingOr[str] = MISSING,
        *,
        spoiler: MissingOr[bool] = MISSING,
        description: str | None = None,
    ) -> None:
        self.buffer: IO[Any]
        """The buffer of this file. You should not mangle this."""

        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError("file buffer must be seekable and readable")
            self.buffer = fp  # type: ignore
            self._original_pos = fp.tell()
            self._owner = False
        else:
            self.buffer = open(fp, "rb")
            self._original_pos = 0
            self._owner = True

        self._close = self.buffer.close
        self.buffer.close = lambda *_: None

        if filename is MISSING:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                name: str = getattr(fp, "name", "untitled")
                filename = name

        self.spoiler: bool = spoiler or filename.startswith("SPOILER_")
        """Whether this file is marked as spoiler."""
        self._filename: str = filename.removeprefix("SPOILER_")
        self.description: str | None = description
        """The file description."""

    @property
    def filename(self) -> str:
        """The clean name of this file."""
        return self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self.spoiler = value.startswith("SPOILER_") or self.spoiler
        self._filename = value.removeprefix("SPOILER_")

    @property
    def uri(self) -> str:
        """Returns a ``attachment://filename`` URI for this file."""
        return f"attachment://{self.filename}"

    def seek(self, pos: int) -> None:
        """Seeks this file to the provided position."""
        self.buffer.seek(pos)

    def reset(self, *, seek: bool = True) -> None:
        """Resets this file to the original position."""
        if seek:
            self.seek(self._original_pos)

    def close(self) -> None:
        """Closes this file buffer."""

        self.buffer.close = self._close
        if self._owner:
            self._close()

    def to_dict(self, idx: int) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "id": idx,
            "filename": self.filename,
        }

        if self.description is not None:
            pd["description"] = self.description
        if self.spoiler:
            pd["flags"] = AttachmentFlags.spoiler.value
        return pd
