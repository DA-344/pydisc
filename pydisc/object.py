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

from typing import TypeVar

from .abc import Snowflake
from .missing import MISSING, MissingOr
from .mixins import Hashable

S = TypeVar("S", bound="Snowflake | Hashable")

__all__ = ("Object",)


class Object(Hashable):
    r"""Represents an object with just an id.

    There are cases in which the library would ask for :class:`abc.Snowflake`\s,
    you can pass this object to pass a model of type :attr:`type` of which you
    only have the ID.
    """

    def __init__(self, *, id: int, type: MissingOr[type[S]] = MISSING) -> None:
        self.id: int = id
        """The ID of the object."""
        self.type: type[Snowflake | Hashable] = type or Object
        """The model type this Object should imitate."""
