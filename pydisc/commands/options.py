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

from enum import Enum
import inspect
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, Union, get_args as _get_args

from pydisc.enums import ChannelType, CommandOptionType, Locale, try_enum
from pydisc.utils import resolve_annotation

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    from pydisc import abc

C = TypeVar("C", int, str, float)


def get_args(annotation: Any) -> tuple[Any, ...]:
    cache = {}
    if isinstance(annotation, str):
        annotation = resolve_annotation(annotation, globals(), locals(), cache)
    return _get_args(annotation)


def handle_enum(enum: type[Enum], args: Any, param: inspect.Parameter) -> tuple[list[Choice[Any]], CommandOptionType]:
    enum_values_type = list(map(type, enum))
    base_enum_value = enum_values_type[0]

    if any(evt is not base_enum_value for evt in enum_values_type[1:]):
        raise TypeError(f"Enum constant values must all be from the same type, {param.name} does not satisfy this.")

    rtyp = CommandOptionType.from_type(base_enum_value)

    choices: list[Choice[Any]] = []

    for en in args:
        choices.append(
            Choice(
                name=en.name,
                value=en.value,
            ),
        )
    return choices, rtyp


def handle_literal(args: tuple[Any, ...], param: inspect.Parameter) -> tuple[list[Choice[Any]] | None, CommandOptionType]:
    base: Any = type(args[0])

    if any(not issubclass(type(c), base) for c in args[1:]):
        raise TypeError(f"Literal values must be all from the same type, {param.name} does not satisfy this.")

    if len(args) == 2 and base is bool:
        return None, CommandOptionType.boolean

    if base is Enum:
        choices, rtyp = handle_enum(base, args, param)
    elif base in (str, int, float):
        rtyp = CommandOptionType.from_type(base)
        choices = []

        for ch in args:
            choices.append(
                Choice(
                    name=str(ch),
                    value=ch,
                ),
            )
    else:
        raise TypeError(f"unsupported Literal types for parameter {param.name}")

    return choices, rtyp


def is_channel(obj: type | object) -> TypeIs[abc.Channel]:
    from pydisc.abc import Channel

    # linter doing linting things
    if isinstance(obj, Channel):
        return True
    return issubclass(obj, Channel)


def resolve_args(annotation: Any, param: inspect.Parameter, default_kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    required = param.default is not param.empty

    kwargs = default_kwargs or {
        "name": param.name,
        "required": required,
    }

    if annotation is Literal:
        args = get_args(annotation)
        kwargs["choices"], kwargs["type"] = handle_literal(args, param)
    elif annotation is Union:
        args = get_args(annotation)

        if type(None) in args:
            kwargs["required"] = required = False
            param.replace(default=None)
            args = tuple(a for a in args if a is not type(None))

        if len(args) == 1:
            arg = type(args[0])

            if arg is Enum:
                kwargs["choices"], kwargs["type"] = handle_enum(arg, args, param)
            elif arg is Literal:
                kwargs["choices"], kwargs["type"] = handle_literal(args, param)
            else:
                raise TypeError(f"unsupported type in Union annotation for {param.name} parameter: {arg}")
        else:
            kwargs["type"] = CommandOptionType.from_type(args)
    else:
        kwargs["type"] = CommandOptionType.from_type(annotation)

    return kwargs


class Option:
    """Represents an application command's option."""

    def __init__(
        self,
        type: CommandOptionType,
        name: str,
        *,
        description: str | None = None,
        required: bool | None = None,
        choices: list[Choice[Any]] | None = None,
        options: list[Option] | None = None,
        channel_types: list[ChannelType] | None = None,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        autocomplete: bool | None = None,
    ) -> None:
        # TODO: maybe add lib-side checks for parameters? idk, if someone wants to do this
        # then have no doubt on pr'ing it.
        self.type: CommandOptionType = type
        """This option's type."""
        self.name: str = name
        """The option name."""
        self.description: str = description or "..."
        """The option description. If ``None`` is provided then it defaults to ``...``."""
        self.required: bool | None = required
        """Whether this option is required."""
        self.choices: list[Choice[Any]] | None = choices
        """This option's static choices."""
        self.options: list[Option] | None = options
        """This option's sub-choices. Only applicable when :attr:`type` is :attr:`CommandOptionType.subcommand` or :attr:`CommandOptionType.subcommand_group`"""
        self.channel_types: list[ChannelType] | None = channel_types
        """The type of the allowed channels users can select. Only applicable when :attr:`type` is :attr:`CommandOptionType.channel`."""
        self.min_value: int | float | None = min_value
        """The minimum number-like (integer or floats) value the user must pass for the option to pass the Discord-side checks."""
        self.max_value: int | float | None = max_value
        """The maximum number-like (integer or float) value the user must pass for the option to pass the Discord-side checks."""
        self.min_length: int | None = min_length
        """The minimum length of the string value (when :attr:`type` is :attr:`CommandOptionType.string`) for the value to pass the Discord-side checks."""
        self.max_length: int | None = max_length
        """The maximum length of the string value (when :attr:`type` is :attr:`CommandOptionType.string`) for the value to pass the Discord-side checks."""
        self.autocomplete: bool | None = autocomplete
        """Whether this option uses autocomplete or not."""
        self.name_localizations: dict[Locale, str] = {}
        """A mapping of :class:`Locale` and :class:`str` that represent the available localizations of this option's name."""
        self.description_localizations: dict[Locale, str] = {}
        """A mapping of :class:`Locale` and :class:`str` that represent the available localizations of this option's description."""
        self._parameter: inspect.Parameter | None = None

    @classmethod
    def from_parameter(
        cls, parameter: inspect.Parameter, globalns: dict[str, Any], localns: dict[str, Any], cache: dict[str, Any]
    ) -> Option:
        if not parameter.annotation or parameter.annotation is parameter.empty:
            raise TypeError(f"application commands must have type annotations, {parameter.name} is missing it")

        resolved = resolve_annotation(parameter.annotation, globalns, localns, cache)
        kwargs = resolve_args(resolved, parameter)

        self = Option(**kwargs)
        self._parameter = parameter
        return self

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
        }

        if self.required is not None:
            pd["required"] = self.required
        if self.name_localizations:
            pd["name_localizations"] = {k.value: v for k, v in self.name_localizations.items()}
        if self.description_localizations:
            pd["description_localizations"] = {k.value: v for k, v in self.description_localizations.items()}
        if self.choices is not None:
            pd["choices"] = [c.to_dict() for c in self.choices]
        if self.options is not None:
            pd["options"] = [o.to_dict() for o in self.options]
        if self.channel_types is not None:
            pd["channel_types"] = [ct.value for ct in self.channel_types]
        if self.min_value is not None:
            pd["min_value"] = self.min_value
        if self.max_value is not None:
            pd["max_value"] = self.max_value
        if self.min_length is not None:
            pd["min_length"] = self.min_length
        if self.max_length is not None:
            pd["max_length"] = self.max_length
        if self.autocomplete is not None:
            pd["autocomplete"] = self.autocomplete
        return pd

    @property
    def parameter(self) -> inspect.Parameter | None:
        """Returns the parameter associated with option in the function's callback."""
        return self._parameter

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Option:
        typ = try_enum(CommandOptionType, data["type"])
        name = data["name"]
        required = data.get("required")
        description = data["description"]

        choices = None
        if choices_data := data.get("choices"):
            choices = [Choice.from_dict(chd) for chd in choices_data]

        options = None
        if options_data := data.get("options"):
            options = [Option.from_dict(opd) for opd in options_data]

        channel_types = None
        if ch_typs_data := data.get("channel_types"):
            channel_types = [try_enum(ChannelType, ch_typ) for ch_typ in ch_typs_data]

        min_value = data.get("min_value")
        max_value = data.get("max_value")
        min_length = data.get("min_length")
        max_length = data.get("max_length")
        autocomplete = data.get("autocomplete")
        self = Option(
            typ,
            name,
            description=description,
            required=required,
            choices=choices,
            channel_types=channel_types,
            options=options,
            min_value=min_value,
            max_value=max_value,
            min_length=min_length,
            max_length=max_length,
            autocomplete=autocomplete,
        )
        self.name_localizations = dict(
            map(
                lambda i: (try_enum(Locale, i[0]), i[1]),
                data.get("name_localizations", {}).items(),
            ),
        )
        self.description_localizations = dict(
            map(
                lambda i: (try_enum(Locale, i[0]), i[1]),
                data.get("description_localizations", {}).items(),
            ),
        )
        return self

    @classmethod
    def from_dict_array(cls, options: list[dict[str, Any]] | None) -> list[Option]:
        if not options:
            return []
        return [Option.from_dict(d) for d in options]


class Choice(Generic[C]):
    """Represents an option's choices."""

    def __init__(
        self,
        name: str,
        value: C,
    ) -> None:
        self.name: str = name
        """The choice displayed name."""
        self.value: C = value
        """The choice value."""
        self.name_localizations: dict[Locale, str] = {}
        """A mapping of :class:`Locale` and :class:`str` that represent the available localizations of this choice's name."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Choice[C]:
        self = Choice(
            name=data["name"],
            value=data["value"],
        )
        self.name_localizations = dict(
            map(
                lambda i: (try_enum(Locale, i[0]), i[1]),
                data.get("name_localizations", {}).items(),
            ),
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "name_localizations": self.name_localizations,
        }
