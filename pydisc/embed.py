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

from collections.abc import Mapping
import datetime
from typing import TYPE_CHECKING, Any, Literal, Protocol, Self

from . import utils
from .color import Color
from .flags import AttachmentFlags, EmbedFlags

EmbedType = Literal["rich", "image", "video", "gifv", "article", "link", "poll_result"]

__all__ = (
    "EmbedType",
    "EmbedProxy",
    "EmbedMediaProxy",
    "Embed",
)


class EmbedProxy:
    def __init__(self, layer: dict[str, Any]) -> None:
        self.__dict__.update(layer)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __getattr__(self, attr: str) -> None:
        return None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EmbedProxy) and self.__dict__ == other.__dict__


class EmbedMediaProxy(EmbedProxy):
    def __init__(self, layer: dict[str, Any]) -> None:
        if "flags" in layer:
            f = layer.pop("flags")
            layer["_flags"] = f
        super().__init__(layer)

    @property
    def flags(self) -> AttachmentFlags:
        return AttachmentFlags(self.__dict__.get("_flags", 0))


if TYPE_CHECKING:

    class _EmbedFooterProxy(Protocol):
        text: str | None
        icon_url: str | None

    class _EmbedFieldProxy(Protocol):
        name: str | None
        value: str | None
        inline: bool

    class _EmbedMediaProxy(Protocol):
        url: str | None
        proxy_url: str | None
        height: int | None
        width: int | None
        flags: AttachmentFlags

    class _EmbedProviderProxy(Protocol):
        name: str | None
        url: str | None

    class _EmbedAuthorProxy(Protocol):
        name: str | None
        url: str | None
        icon_url: str | None
        proxy_icon_url: str | None


class Embed:
    """Represents a Discord embed."""

    __fields__ = (
        "_timestamp",
        "_color",
        "_footer",
        "_image",
        "_thumbnail",
        "_video",
        "_provider",
        "_author",
        "_fields",
        "_flags",
    )

    def __init__(
        self,
        *,
        color: Color | None = None,
        title: str | None = None,
        type: EmbedType = "rich",
        url: str | None = None,
        description: str | None = None,
        timestamp: datetime.datetime | None = None,
    ) -> None:
        self.color = color
        self.title: str | None = title
        self.type: EmbedType = type
        self.url: str | None = url
        self.description: str | None = description
        self._flags: int = 0

        if timestamp is not None:
            self.timestamp = timestamp

    def copy(self) -> Self:
        """Returns a copy of this embed."""
        return self.__class__.from_dict(self.to_dict())

    def __len__(self) -> int:
        total = len(self.title or "") + len(self.description or "")
        for field in getattr(self, "_fields", []):
            total += len(field["name"]) + len(field["value"])

        try:
            footer = self._footer["text"]
        except (AttributeError, KeyError):
            pass
        else:
            total += len(footer)

        try:
            author = self._author["name"]
        except (AttributeError, KeyError):
            pass
        else:
            total += len(author)

        return total

    def __bool__(self) -> bool:
        return any(
            (
                self.title,
                self.url,
                self.description,
                self.color,
                self.fields,
                self.timestamp,
                self.author,
                self.thumbnail,
                self.footer,
                self.image,
                self.provider,
                self.video,
            )
        )

    def __eq__(self, other: Embed) -> bool:
        return isinstance(other, Embed) and (
            self.type == other.type
            and self.title == other.title
            and self.url == other.url
            and self.description == other.description
            and self.color == other.color
            and self.fields == other.fields
            and self.timestamp == other.timestamp
            and self.author == other.author
            and self.thumbnail == other.thumbnail
            and self.footer == other.footer
            and self.image == other.image
            and self.provider == other.provider
            and self.video == other.video
            and self._flags == other._flags
        )

    @property
    def timestamp(self) -> datetime.datetime | None:
        """The timestamp set to this embed."""
        return getattr(self, "_timestamp", None)

    @timestamp.setter
    def timestamp(self, value: datetime.datetime | None) -> None:
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.astimezone()
            self._timestamp = value
        elif value is None:
            self._timestamp = None
        else:
            raise TypeError(f"expected a datetime.datetime object or None, got {value.__class__.__name__}")

    @property
    def flags(self) -> EmbedFlags:
        """Returns the flags of this embed."""
        return EmbedFlags(self._flags)

    @property
    def color(self) -> Color | None:
        """The accent color of this embed. Shown in the left side."""
        return getattr(self, "_color", None)

    @color.setter
    def color(self, value: Color | None) -> None:
        if value is None:
            self._color = None
        elif isinstance(value, Color):
            self._color = value
        else:
            raise TypeError(f"expected a Color object or None, got {value.__class__.__name__}")

    @property
    def footer(self) -> _EmbedFooterProxy:
        """Returns a proxy for this embed footer."""
        return EmbedProxy(getattr(self, "_footer", {}))  # pyright: ignore[reportReturnType]

    def set_footer(
        self,
        *,
        text: str | None = None,
        icon_url: str | None = None,
    ) -> Self:
        """Sets a footer to this embed."""
        self._footer = {}
        if text is not None:
            self._footer["text"] = text
        if icon_url is not None:
            self._footer["icon_url"] = icon_url
        return self

    def remove_footer(self) -> Self:
        """Clears this embed footer."""
        try:
            del self._footer
        except AttributeError:
            pass
        return self

    @property
    def image(self) -> _EmbedMediaProxy:
        """Returns a proxy for this embed image."""
        return EmbedProxy(getattr(self, "_image", {}))  # pyright: ignore[reportReturnType]

    def set_image(self, *, url: str) -> Self:
        """Sets an image to this embed."""
        self._image = {"url": url}
        return self

    def remove_image(self) -> Self:
        """Clears this embed image."""
        try:
            del self._image
        except AttributeError:
            pass
        return self

    @property
    def thumbnail(self) -> _EmbedMediaProxy:
        """Returns a proxy for this embed thumbnail."""
        return EmbedProxy(getattr(self, "_thumbnail", {}))  # pyright: ignore[reportReturnType]

    def set_thumbnail(self, *, url: str) -> Self:
        """Sets a thumbnail to this embed."""
        self._thumbnail = {"url": url}
        return self

    def remove_thumbnail(self) -> Self:
        """Clears this embed thumbnail."""
        try:
            del self._thumbnail
        except AttributeError:
            pass
        return self

    @property
    def video(self) -> _EmbedMediaProxy:
        """Returns a proxy for this embed video."""
        return EmbedProxy(getattr(self, "_video", {}))  # pyright: ignore[reportReturnType]

    @property
    def provider(self) -> _EmbedProviderProxy:
        """Returns a proxy for this embed provider contents."""
        return EmbedProxy(getattr(self, "_provider", {}))  # pyright: ignore[reportReturnType]

    @property
    def author(self) -> _EmbedAuthorProxy:
        """Returns a proxy for this embed author."""
        return EmbedProxy(getattr(self, "_author", {}))  # pyright: ignore[reportReturnType]

    def set_author(
        self,
        *,
        name: str,
        url: str | None = None,
        icon_url: str | None = None,
    ) -> Self:
        """Sets an author for this embed."""
        self._author = {
            "name": name,
        }
        if url is not None:
            self._author["url"] = url
        if icon_url is not None:
            self._author["icon_url"] = icon_url
        return self

    def remove_author(self) -> Self:
        """Clears this embed author."""
        try:
            del self._author
        except AttributeError:
            pass
        return self

    @property
    def fields(self) -> list[_EmbedFieldProxy]:
        """Returns a proxy for this embed fields."""
        return [EmbedProxy(d) for d in getattr(self, "_fields", [])]  # pyright: ignore[reportReturnType]

    def add_field(self, *, name: str, value: str, inline: bool = True) -> Self:
        """Adds a field to this embed."""

        field = {
            "inline": inline,
            "name": name,
            "value": value,
        }

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]
        return self

    def insert_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> Self:
        """Inserts a new field at index ``index``."""

        field = {
            "inline": inline,
            "name": name,
            "value": value,
        }

        try:
            self._fields.insert(index, field)
        except AttributeError:
            self._fields = [field]
        return self

    def remove_field(self, index: int) -> Self:
        """Removes a field from this embed at index ``index``."""
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass
        return self

    def set_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> Self:
        """Updates a field at index ``index``."""
        try:
            field = self._fields[index]
        except (TypeError, IndexError, AttributeError):
            raise IndexError("field index out of range")

        field["name"] = name
        field["value"] = value
        field["inline"] = inline
        return self

    def clear_fields(self) -> Self:
        """Clears all fields on this embed."""
        try:
            self._fields.clear()
        except AttributeError:
            self._fields = []
        return self

    def to_dict(self) -> dict[str, Any]:
        """Converts this embed object into a dict."""

        result = {key[1:]: getattr(self, key) for key in Embed.__fields__ if hasattr(self, key)}

        try:
            color = result.pop("color")
        except KeyError:
            pass
        else:
            if color:
                result["color"] = color.value

        try:
            timestamp = result.pop("timestamp")
        except KeyError:
            pass
        else:
            if timestamp:
                if timestamp.tzinfo:
                    result["timestamp"] = timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                else:
                    result["timestamp"] = timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()

        # add in the non raw attribute ones
        if self.type:
            result["type"] = self.type

        if self.description:
            result["description"] = self.description

        if self.url:
            result["url"] = self.url

        if self.title:
            result["title"] = self.title

        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Converts a :class:`dict` to a :class:`Embed` provided it is in the
        format that Discord expects it to be in.
        """

        self = cls.__new__(cls)

        self.title = data.get("title", None)
        self.type = data.get("type", None)
        self.description = data.get("description", None)
        self.url = data.get("url", None)
        self._flags = data.get("flags", 0)

        if self.title is not None:
            self.title = str(self.title)

        if self.description is not None:
            self.description = str(self.description)

        if self.url is not None:
            self.url = str(self.url)

        try:
            self._color = Color(value=data["color"])
        except KeyError:
            pass

        try:
            self._timestamp = utils.parse_time(data['timestamp'])
        except KeyError:
            pass

        for attr in ("thumbnail", "video", "provider", "author", "fields", "image", "footer"):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, f"_{attr}", value)

        return self

    @classmethod
    def from_dict_array(cls, data: list[Mapping[str, Any]] | None) -> list[Embed]:
        if not data:
            return []
        return [Embed.from_dict(d) for d in data]
