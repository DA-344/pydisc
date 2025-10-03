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

import colorsys
import re

RGB_REGEX = re.compile(r"rgb\s*\((?P<r>[0-9.]+%?)\s*,\s*(?P<g>[0-9.]+%?)\s*,\s*(?P<b>[0-9.]+%?)\s*\)")

__all__ = (
    "Color",
    "parse_hex_number",
    "parse_rgb",
    "parse_rgb_number",
)


class Color:
    """Represents a Discord color.
    """

    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"expected an int, got a {value.__class__.__name__}")
        self.value: int = value

    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xFF

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return other.value == self.value

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return other.value != self.value

    def __str__(self) -> str:
        return f"#{self.value:0>6x}"

    def __int__(self) -> int:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def r(self) -> int:
        """Returns the red component of the color."""
        return self._get_byte(2)

    @property
    def g(self) -> int:
        """Returns the green component of the color."""
        return self._get_byte(1)

    @property
    def b(self) -> int:
        """Returns the blue component of the color."""
        return self._get_byte(0)

    def to_rgb(self) -> tuple[int, int, int]:
        """Returns a (r, g, b) tuple of this color."""
        return self.r, self.g, self.b

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        """Creates a Color from a (r, g, b) tuple."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Color:
        """Creates a Color from a HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def from_str(cls, value: str) -> Color:
        """Creates a Color from a string of the following supported strings:

        - ``0x<hex>``
        - ``#<hex>``
        - ``0x#<hex>``
        - ``rgb(<number>, <number>, <number>)``

        Like CSS, ``<number>`` can be either 0-255 or 0-100% and ``<hex>`` can be
        either a 6 digit hex number or a 3 digit hex shortcut (e.g. #FFF).
        """

        if not value:
            raise ValueError("unknown color format given")

        if value[0] == "#":
            return parse_hex_number(value[1:])

        if value[0:2] == "0x":
            rest = value[2:]
            if rest.startswith("#"):
                return parse_hex_number(rest[1:])
            return parse_hex_number(rest)

        arg = value.lower()
        if arg[0:3] == "rgb":
            return parse_rgb(arg)

        raise ValueError("unknown color format given")


def parse_hex_number(argument: str) -> Color:
    arg = ''.join(i * 2 for i in argument) if len(argument) == 3 else argument

    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError("hex number out of range for 24-bit color.")
    except ValueError:
        raise ValueError("invalid hex digit given")
    else:
        return Color(value=value)


def parse_rgb_number(number: str) -> int:
    if number[-1] == "%":
        value = float(number[:-1])
        if not (0 <= value <= 100):
            raise ValueError("rgb percentage out of range, not in [0, 100] interval.")
        return round(255 * (value / 100))

    value = int(number)
    if not (0 <= value <= 255):
        raise ValueError("rgb number out of range, not in [0, 255] interval.")
    return value


def parse_rgb(argument: str, *, regex: re.Pattern[str] = RGB_REGEX) -> Color:
    match = regex.match(argument)
    if match is None:
        raise ValueError("invalid rgb syntax found")

    red = parse_rgb_number(match.group("r"))
    green = parse_rgb_number(match.group("g"))
    blue = parse_rgb_number(match.group("b"))
    return Color.from_rgb(red, green, blue)
