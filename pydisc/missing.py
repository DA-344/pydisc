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

from enum import Enum, auto
from typing import Generic, Literal, TypeVar, Union

T = TypeVar("T")
V = TypeVar("V")

__all__ = (
    "MISSING",
    "MissingOr",
    "MissingObject",
)


class Undefined(Enum):
    MISSING = auto()

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Literal[Undefined.MISSING] = Undefined.MISSING
MissingOr = Union[Literal[Undefined.MISSING], T]


class MissingObject(Generic[T]):
    """A helper method to wrap and unwrap missing objects safely.

    When an object is unwrapped but its value is MISSING then this raises
    a ValueError.

    This is similar to the ``Option`` kwarg on Rust.
    """

    def __init__(self, initial: MissingOr[T]) -> None:
        self.value: MissingOr[T] = initial

    def unwrap(self) -> T:
        if self.value is MISSING:
            raise ValueError(f"{self} is MISSING")
        return self.value

    def unwrap_or(self, value: V) -> T | V:
        if self.value is MISSING:
            return value
        return self.value

    def has_value(self) -> bool:
        return self.value is not MISSING

    def set(self, value: MissingOr[T]) -> None:
        self.value = value
