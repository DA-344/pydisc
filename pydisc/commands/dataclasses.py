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

import inspect
from collections.abc import Callable, Coroutine, Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydisc.enums import CommandType

from .options import Option

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from pydisc import abc
    from pydisc.interactions import AutocompleteInteraction, CommandInteraction

    from .cog import Cog
    from .options import Choice

    P = ParamSpec("P")
    T = TypeVar("T")
    CommandCallback = (
        Callable[[Concatenate[CommandInteraction, P]], Coroutine[Any, Any, T]]
        | Callable[[Concatenate[Cog, CommandInteraction, P]], Coroutine[Any, Any, T]]
    )
    AutocompleteCallback = Callable[[AutocompleteInteraction, Any], list[Choice[Any]]]


class Command(Generic[P, T]):
    """Represents a local-side command."""

    def __init__(
        self,
        *,
        callback: CommandCallback[P, T],
        cog: Cog | None = None,
        name: str | None = None,
        description: str | None = None,
        guilds: Sequence[abc.Snowflake] | None = None,
        type: CommandType = CommandType.chat_input,
    ) -> None:
        if not inspect.iscoroutinefunction(callback):
            raise TypeError("command callbacks must be coroutines")

        if isinstance(callback, (staticmethod, classmethod)):
            raise TypeError("command callbacks can not be static- or class- methods")

        self.callback: CommandCallback[P, T] = callback
        """The command's callback. You should consider using :meth:`invoke` instead."""
        self.name: str = name or callback.__name__
        """The command's name."""
        self.description: str = description or callback.__doc__ or "..."
        """The command's description."""
        self._cog: Cog | None = cog
        self.guilds: Sequence[abc.Snowflake] | None = guilds
        """The guilds this command is bound to."""
        self._type: CommandType = type
        self._options: list[Option] = self._get_options()

    @property
    def type(self) -> CommandType:
        """The type of this command."""
        return self._type

    @property
    def cog(self) -> Cog | None:
        """Returns the attached cog of this command."""
        return self._cog

    def _get_options(self) -> list[Option]:
        required_params = 1  # interaction
        if self._cog is not None:
            required_params = 2  # cog, interaction

        try:
            params = inspect.signature(
                self.callback,
                eval_str=True,  # prevent ForwardRef's, although we already handle it in Option
            )
        except:  # TODO: check whether inspect.signature raises any error and if so handle it instead of a bare-except
            # if it fails then we try getting the parameters w/o eval'ing the str annotations,
            # if it fails again here then just raise it
            params = inspect.signature(
                self.callback,
                eval_str=False,
            )

        params_iter = iter(params.parameters.values())

        for _ in range(required_params):
            try:
                next(params_iter)
            except StopIteration:
                raise SyntaxError(
                    "a required parameter (cog [if in a cog context] or interaction) is missing from the command's parameters"
                )

        cache = {}
        options = [Option.from_parameter(parameter, globals(), locals(), cache) for parameter in params_iter]
        return options


class ContextMenu(Command[P, T]):
    """Represents a local-side context menu command."""

    def __init__(
        self,
        *,
        callback: CommandCallback[P, T],
        cog: Cog | None = None,
        name: str | None = None,
        description: str | None = None,
        guilds: Sequence[abc.Snowflake] | None = None,
    ) -> None:
        super().__init__(
            callback=callback,
            cog=cog,
            name=name,
            description=description,
            guilds=guilds,
        )

    def _get_options(self) -> list[Option]:
        required_params = 1  # interaction
        if self._cog is not None:
            required_params = 2

        try:
            params = inspect.signature(
                self.callback,
                eval_str=True,
            )
        except:
            params = inspect.signature(
                self.callback,
                eval_str=False,
            )

        params_iter = iter(params.parameters.values())

        for _ in range(required_params):
            try:
                next(params_iter)
            except StopIteration:
                raise SyntaxError(
                    "a required parameter (cog [if in a cog context] or interaction) is missing from the context menu's parameters"
                )

        remaining = list(params_iter)

        if len(remaining) > 1:
            # context menu commands can either take message or user, not more than one parameter
            raise SyntaxError(
                f"context menu callbacks take 2 parameters, interaction and user/message, or 3 if in a cog context, not {len(remaining)}"
            )

        uom = remaining[0]

        if not uom.annotation or uom.annotation is uom.empty:
            raise SyntaxError(
                "context menu last parameter must be typed with abc.User, User, Member, User | Member, or Message"
            )

        ann = uom.annotation

        from pydisc import Message
        from pydisc.abc import User as AbcUser

        if issubclass(ann, AbcUser):
            self._type = CommandType.user
        elif issubclass(ann, Message):
            self._type = CommandType.message
        else:
            raise TypeError(f"invalid annotation provided {ann}, expected Message, abc.User, User, Member, User | Member")

        return []
