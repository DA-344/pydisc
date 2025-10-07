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

import zlib
from typing import Protocol

try:
    import zstandard  # pyright: ignore[reportMissingImports]
except ImportError:
    _HAS_ZSTD = False
else:
    _HAS_ZSTD = True

__all__ = (
    "Decompressor",
    "ActiveDecompressor",
)


class Decompressor(Protocol):
    COMPRESSION_TYPE: str

    def decompress(self, data: bytes, /) -> str | None: ...


ActiveDecompressor: type[Decompressor]

if _HAS_ZSTD:

    class _ZstdDecompressionContext:
        __slots__ = ("context",)

        COMPRESSION_TYPE: str = "zstd-stream"

        def __init__(self) -> None:
            decompressor = (
                zstandard.ZstdDecompressor()
            )  # pyright: ignore[reportUnknownMemberType, reportPossiblyUnboundVariable, reportUnknownVariableType]
            self.context = decompressor.decompressobj()  # pyright: ignore[reportUnknownMemberType]

        def decompress(self, data: bytes, /) -> str | None:
            return self.context.decompress(data).decode(
                "utf-8"
            )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    ActiveDecompressor = _ZstdDecompressionContext
else:

    class _ZlibDecompressionContext:
        __slots__ = ("context", "buffer")

        COMPRESSION_TYPE: str = "zlib-stream"

        def __init__(self) -> None:
            self.buffer: bytearray = bytearray()
            self.context = zlib.decompressobj()

        def decompress(self, data: bytes, /) -> str | None:
            self.buffer.extend(data)

            if len(data) < 4 or data[-4:] != b"\x00\x00\xff\xff":
                return

            msg = self.context.decompress(self.buffer)
            self.buffer = bytearray()
            return msg.decode("utf-8")

    ActiveDecompressor = _ZlibDecompressionContext
