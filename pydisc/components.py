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

from collections.abc import Generator
import os
from typing import TYPE_CHECKING, Any, Literal, Self, overload

from .enums import ButtonStyle, ComponentType, try_enum
from .emoji import Emoji

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .interactions import Interaction

__all__ = (
    "_pd_to_component",
    "Component",
    "UnknownComponent",
    "ActionRow",
    "Button",
)


def _pd_to_component(payload: dict[str, Any], cache: CacheProtocol) -> Component:
    typ = int(payload["type"])

    if typ not in ComponentType:
        return UnknownComponent(typ, payload)

    if typ == ComponentType.action_row:
        return ActionRow.from_dict(payload, cache)
    elif typ == ComponentType.button:
        return Button.from_dict(payload, cache)
    else:
        return UnknownComponent(typ, payload)


class Component:
    """Represents a Discord component."""

    def __init__(self) -> None:
        self._id: int | None = None

    @property
    def type(self) -> ComponentType:
        """Returns the type of this component."""
        raise NotImplementedError

    @property
    def id(self) -> int | None:
        """Returns this component's ID, or ``None`` if not set."""
        return self._id

    @id.setter
    def id(self, value: int | None) -> None:
        self._id = value

    @property
    def weight(self) -> int:
        r"""How much space this items takes. Only applicable
        on :class:`ActionRow` children.
        """
        return 1

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict[str, Any], cache: CacheProtocol) -> Self:
        raise NotImplementedError

    def _update(self, data: dict[str, Any]) -> None:
        return None

    @overload
    def get_component(self, *, id: int) -> Component | None: ...

    @overload
    def get_component(self, *, custom_id: str) -> Component | None: ...

    @overload
    def get_component(self, *, id: int, custom_id: str) -> Component | None: ...

    def get_component(
        self,
        *,
        id: int | None = None,
        custom_id: str | None = None,
    ) -> Component | None:
        """Returns a component with the provided ``id`` or ``custom_id``.

        This uses :meth:`.walk_components` to iterate through all the components.

        You must provide AT LEAST one of ``id`` or ``custom_id``.

        Raises
        ------
        TypeError
            You did not provide any of ``id`` or ``custom_id``.

        Returns
        -------
        :class:`Component` | :data:`None`
            The component with the provided data, or ``None``.
        """

        if id is None and custom_id is None:
            raise TypeError("you must specify any of id or custom_id, or both")

        for comp in self.walk_components():
            if id is not None and comp.id == id:
                return comp
            if custom_id is not None and getattr(comp, "custom_id", None) == custom_id:
                return comp
        return None

    def walk_components(self) -> Generator[Component, None, None]:
        """Yields all this components nested components.

        If the current component does not have nested components, returns the class
        instance itself.
        """
        yield self

    def is_dispatchable(self) -> bool:
        """Whether this component can be interacted with."""
        return False

    def is_v2(self) -> bool:
        """Whether this component is part of the Components V2"""
        return False


class UnknownComponent(Component):
    """Represents an unknown component type.

    This differs from :class:`Component` because :attr:`.type` is
    an integer denoting the unknown component type.

    This offers a :attr:`.data` attribute that contains the raw received
    data from the API.
    """

    def __init__(self, type: int, data: dict[str, Any]) -> None:
        self._type: ComponentType = try_enum(ComponentType, type)
        self._data: dict[str, Any] = data

    @property
    def type(self) -> ComponentType:
        return self._type

    @property
    def data(self) -> dict[str, Any]:
        """The raw data received from the API."""
        return self._data.copy()


class ActionRow(Component):
    """Represents an Action Row component (type 1).

    This can hold any of the following:
    - 5 buttons
    - 1 select (of any type)
    """

    def __init__(
        self,
        *components: Component,
        id: int | None = None,
    ) -> None:
        if len(components) > 5:
            raise ValueError("action rows can have up to 5 children")
        if sum(c.weight for c in components) > 5:
            raise ValueError("maximum children weight exceeded, this can take only up 5 buttons OR 1 select (of any type)")

        super().__init__()
        self.id = id
        self._components: list[Component] = list(components)

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "type": self.type.value,
            "components": [c.to_dict() for c in self._components],
        }
        if self.id is not None:
            pd["id"] = self.id
        return pd

    @classmethod
    def from_dict(cls, data: dict[str, Any], cache: CacheProtocol) -> ActionRow:
        components = [_pd_to_component(c, cache) for c in data["components"]]
        return ActionRow(*components, id=data.get("id"))

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        return ComponentType.action_row

    @property
    def current_weight(self) -> int:
        """Returns the current children's weight on this row."""
        return sum(c.weight for c in self._components)

    @property
    def components(self) -> list[Component]:
        """Returns a list of this action row's components.

        This is a shortcut for converting :meth:`.walk_components` into
        a :class:`list`.
        """
        return list(self.walk_components())

    def add_component(self, component: Component, /) -> Self:
        """Adds a component to this Action Row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        component: :class:`Component`
            The component to add to this action row.

        Raises
        ------
        ValueError
            The maximum weight of this row has been exceeded.
        TypeError
            You did not pass a Component instance.
        """

        if not isinstance(component, Component):
            raise TypeError(f"expected a Component instance, got {component.__class__.__name__!r}")

        if self.current_weight + component.weight > 5:
            raise ValueError(
                "maximum children weight has been exceeded, this can take only up to 5 buttons OR 1 select (of any type)"
            )

        self._components.append(component)
        return self

    def remove_component(self, component: Component, /) -> Self:
        """Removes a component from this Action Row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        component: :class:`Component`
            The component to remove from this action row.
        """

        try:
            self._components.remove(component)
        except ValueError:
            pass

        return self

    def walk_components(self) -> Generator[Component, None, None]:
        yield from self._components


class _CustomIdComponent(Component):
    def __init__(self, custom_id: str | None) -> None:
        self._provided_custom_id: bool = custom_id is not None
        self._custom_id: str = custom_id if custom_id is not None else self._generate_custom_id()

    def _generate_custom_id(self) -> str:
        return os.urandom(16).hex()

    @property
    def custom_id(self) -> str:
        """Returns the custom ID of this component, used to identify
        the component when receiving interactions.
        """
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: str | None) -> None:
        if value is None:
            value = self._generate_custom_id()
        self._custom_id = value


class Button(_CustomIdComponent):
    """Represents a Button."""

    if TYPE_CHECKING:
        _custom_id: str | None

    @overload
    def __init__(
        self,
        *,
        style: Literal[ButtonStyle.premium, ButtonStyle.sku] = ...,
        id: int | None = ...,
        sku_id: int,
        disabled: bool = ...,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        style: Literal[ButtonStyle.url, ButtonStyle.link] = ...,
        id: int | None = ...,
        url: str,
        disabled: bool = ...,
        label: str | None = ...,
        emoji: str | Emoji | None = ...,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        style: Literal[
            ButtonStyle.primary,
            ButtonStyle.blurple,
            ButtonStyle.secondary,
            ButtonStyle.grey,
            ButtonStyle.gray,
            ButtonStyle.danger,
            ButtonStyle.red,
            ButtonStyle.success,
            ButtonStyle.green,
        ] = ...,
        label: str | None = ...,
        emoji: str | Emoji | None = ...,
        custom_id: str | None = ...,
        id: int | None = ...,
        disabled: bool = ...,
    ) -> None: ...

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        id: int | None = None,
        label: str | None = None,
        emoji: str | Emoji | None = None,
        custom_id: str | None = None,
        sku_id: int | None = None,
        url: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(custom_id)

        if url is not None:
            style = ButtonStyle.url
            self._custom_id = None
        if sku_id is not None:
            style = ButtonStyle.premium
            self._custom_id = None

        self._requires_custom_id: bool = url is None and sku_id is None
        self._style: ButtonStyle = style
        self.label: str | None = label
        self.emoji: str | Emoji | None = emoji
        self.sku_id: int | None = sku_id
        self.url: str | None = url
        self.disabled: bool = disabled

        self.id = id

    @property
    def custom_id(self) -> str | None:
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: str | None) -> None:
        if value is None and self._requires_custom_id:
            self._custom_id = self._generate_custom_id()
        else:
            self._custom_id = value

    @property
    def style(self) -> ButtonStyle:
        """Returns the style of this button. If you want to change a button's
        style, then you should recreate it.
        """
        return self._style

    @property
    def type(self) -> Literal[ComponentType.button]:
        return ComponentType.button

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "type": self.type.value,
            "style": self.style.value,
            "disabled": self.disabled,
        }

        if self.label is not None:
            pd["label"] = self.label
        if self.emoji is not None:
            if isinstance(self.emoji, str):
                emoji = {"name": self.emoji}
            else:
                emoji = self.emoji.to_dict()

            pd["emoji"] = emoji
        if self.sku_id is not None:
            pd["sku_id"] = str(self.sku_id)
        if self.url is not None:
            pd["url"] = self.url
        return pd

    @classmethod
    def from_dict(cls, data: dict[str, Any], cache: CacheProtocol) -> Button:
        style: ButtonStyle = try_enum(
            ButtonStyle,
            data["style"],
        )

        emoji: Emoji | None = None

        if emoji_data := data.get("emoji"):
            emoji = Emoji.from_dict(emoji_data, cache)

        return Button(
            style=style,  # pyright: ignore[reportArgumentType]
            label=data.get("label"),
            emoji=emoji,
        )

    def is_dispatchable(self) -> bool:
        return True

    async def callback(self, interaction: Interaction, /) -> None:
        """The callback of this button.

        This must be overridden in order to implement custom logic.

        By default, this raises a :exc:`NotImplementedError`.
        """
        raise NotImplementedError
