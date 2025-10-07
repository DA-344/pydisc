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

import datetime
import typing
from base64 import b64decode, b64encode
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from enum import Flag
from functools import partial
from operator import attrgetter
from typing import TYPE_CHECKING, Any, ClassVar, ForwardRef, Generic, Literal, TypeVar, Union, overload

try:
    from orjson import dumps as __to_json, loads as _from_json  # type: ignore

    def _to_json(obj: Any) -> str:
        return __to_json(obj).decode("utf-8")  # type: ignore

except ImportError:
    from json import dumps as __to_json, loads as _from_json

    def _to_json(obj: Any) -> str:
        return __to_json(obj, separators=(",", ":"), ensure_ascii=True)


if TYPE_CHECKING:
    _from_json: Callable[..., Any]

C = TypeVar("C", bound="Protocol", covariant=True)
F = TypeVar("F", bound=Flag)
FR = TypeVar("FR", bound=Flag)
T = TypeVar("T")


DISCORD_EPOCH = 1420070400000

__all__ = (
    "_from_json",
    "_to_json",
    "_get_snowflake",
    "flatten_literal_params",
    "normalise_optional_params",
    "evaluate_annotation",
    "resolve_annotation",
    "_iter_proto_names",
    "ProtocolMeta",
    "Protocol",
    "checkable_protocol",
    "ClassProperty",
    "class_property",
    "parse_time",
    "snowflake_to_time",
    "time_to_snowflake",
    "find",
    "get",
    "base64_to_bytes",
    "get_image_mime_type",
    "get_audio_mime_type",
    "bytes_to_base64",
)


def _get_snowflake(key: str, mapping: dict[str, Any]) -> int | None:
    if value := mapping.get(key):
        return value and int(value)
    return None


def flatten_literal_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    params: list[Any] = []
    literal_cls = type(Literal[0])
    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(p.__args__)  # type: ignore
        else:
            params.append(p)
    return tuple(params)


def normalise_optional_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    none_cls = type(None)
    return tuple(p for p in parameters if p is not none_cls) + (none_cls,)


def evaluate_annotation(
    tp: Any,
    globals: dict[str, Any],
    locals: dict[str, Any],
    cache: dict[str, Any],
    *,
    implicit_str: bool = True,
) -> Any:
    if isinstance(tp, ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = evaluate_annotation(eval(tp, globals, locals), globals, locals, cache)
        cache[tp] = evaluated
        return evaluated

    if getattr(tp.__repr__, '__objclass__', None) is typing.TypeAliasType:  # type: ignore
        temp_locals = dict(**locals, **{t.__name__: t for t in tp.__type_params__})
        annotation = evaluate_annotation(tp.__value__, globals, temp_locals, cache.copy())
        if hasattr(tp, '__args__'):
            annotation = annotation[tp.__args__]
        return annotation

    if hasattr(tp, '__supertype__'):
        return evaluate_annotation(tp.__supertype__, globals, locals, cache)

    if hasattr(tp, '__metadata__'):
        # Annotated[X, Y] can access Y via __metadata__
        metadata = tp.__metadata__[0]
        return evaluate_annotation(metadata, globals, locals, cache)

    if hasattr(tp, '__args__'):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, '__origin__'):
            return tp
        if tp.__origin__ is Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is Literal:
            args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str) for arg in args)

        if is_literal and not all(isinstance(x, (str, int, bool, type(None))) for x in evaluated_args):
            raise TypeError('Literal arguments must be of type str, int, bool, or NoneType.')

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]

    return tp


def resolve_annotation(
    annotation: Any,
    globalns: dict[str, Any],
    localns: dict[str, Any] | None,
    cache: dict[str, Any] | None,
) -> Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)


def _iter_proto_names(proto: type) -> set[str]:
    anns = set(ProtocolMeta.__get_annotations__(proto))
    dict_names = {k for k in proto.__dict__.keys() if not k.startswith("__")}  # no dunders
    return anns | dict_names


class ProtocolMeta(type):
    __runtime_checkable__: ClassVar[bool] = False

    @staticmethod
    def __get_annotations__(proto: type[Protocol] | ProtocolMeta) -> dict[str, Any]:
        anns = dict(proto.__annotations__)
        anns.pop("__runtime_checkable__", None)
        return anns

    def __instancecheck__(self, instance: Any, /) -> bool:
        if not self.__runtime_checkable__:
            raise RuntimeError("Protocols that are checked must be marked with the checkable_protocol decorator")

        for name in _iter_proto_names(self):
            if not hasattr(instance, name):
                return False
        return True

    def __subclasscheck__(self, subclass: type, /) -> bool:
        if not self.__runtime_checkable__:
            raise RuntimeError("Protocols that are checked must be marked with the checkable_protocol decorator")

        other = _iter_proto_names(subclass)
        for name in _iter_proto_names(self):
            if name not in other:
                return False
        return True


class Protocol(metaclass=ProtocolMeta):

    @classmethod
    def is_instance(cls, other: object) -> bool:
        return isinstance(other, cls)

    @classmethod
    def is_subclass(cls, other: type) -> bool:
        return issubclass(other, cls)


# who the fuck decided Protocols with non-method attributes are
# not runtime-checkable.
def checkable_protocol(cls: type[C]) -> type[C]:
    if not issubclass(cls, Protocol):
        raise TypeError(f"expected a Protocol, got {cls}")
    cls.__runtime_checkable__ = True
    return cls


class ClassProperty(Generic[F, FR]):
    def __init__(self, func: Callable[[type[F]], FR]) -> None:
        self._func: Callable[[type[F]], FR] = func
        self.__doc__ = func.__doc__

    @overload
    def __get__(self, inst: None, owner: type[F]) -> FR: ...

    @overload
    def __get__(self, inst: F, owner: type[F]) -> FR: ...

    def __get__(self, inst: F | None, owner: type[F]) -> FR:
        return self._func(owner)

    def __set__(self, inst: F, value: bool) -> None:
        if value is True:
            inst |= self._func(type(inst))
        elif value is False:
            inst &= ~(self._func(type(inst)))  # type: ignore
        else:
            raise TypeError("value to set for {self._func.__name__} must be a boolean")


def class_property(func: Callable[[F], FR]) -> ClassProperty[F, FR]:
    return ClassProperty(func)  # type: ignore


@overload
def parse_time(dt: None) -> None: ...


@overload
def parse_time(dt: str) -> datetime.datetime: ...


def parse_time(dt: str | None) -> datetime.datetime | None:
    """Parses a datetime string into a datetime.datetime object."""
    if dt:
        return datetime.datetime.fromisoformat(dt)
    return None


def snowflake_to_time(id: int, /) -> datetime.datetime:
    """Converts an ID to a :class:`datetime.datetime` object."""
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def time_to_snowflake(dt: datetime.datetime, /, *, high: bool = False) -> int:
    """Converts a :class:`datetime.datetime` object into an ID."""
    discord_millis = int(dt.timestamp() * 1000 - DISCORD_EPOCH)
    return (discord_millis << 22) + (2**22 - 1 if high else 0)


def _find(iter: Iterable[T], pred: Callable[[T], bool], count: int | None) -> list[T]:
    ret: list[T] = []
    for item in iter:
        if pred(item):
            ret.append(item)

            if count is not None and len(ret) >= count:
                break
    return ret


async def _afind(iter: AsyncIterable[T], pred: Callable[[T], bool], count: int | None) -> list[T]:
    ret: list[T] = []
    async for item in iter:
        if pred(item):
            ret.append(item)

            if count is not None and len(ret) >= count:
                break
    return ret


def _get_pred(item: Any, attrs: dict[str, Any]) -> bool:
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrgetter(k.replace("__", "."))
        return pred(item) == v

    conv = [(attrgetter(attr.replace("__", ".")), value) for attr, value in attrs.items()]
    return all(pred(item) == value for pred, value in conv)


@overload
def find(predicate: Callable[[T], bool], iterable: Iterable[T], *, count: int = ...) -> list[T]: ...


@overload
async def find(predicate: Callable[[T], bool], iterable: AsyncIterable[T], *, count: int = ...) -> list[T]: ...


def find(
    predicate: Callable[[T], bool], iterable: Iterable[T] | AsyncIterable[T], *, count: int | None = None
) -> list[T] | Coroutine[None, None, list[T]]:
    """Returns ``count`` (or all) items in ``iterable`` that meet ``predicate``.

    If ``iterable`` is an :class:`collections.abc.AsyncIterable`, then this returns a coroutine.
    """
    if isinstance(iterable, AsyncIterable):
        return _afind(iterable, predicate, count)
    else:
        return _find(iterable, predicate, count)


async def _aget(iterable: AsyncIterable[T], attrs: dict[str, Any]) -> T | None:
    ret: list[T] = await find(partial(_get_pred, attrs=attrs), iterable, count=1)
    if not ret:
        return None
    return ret[0]


def _get(iterable: Iterable[T], attrs: dict[str, Any]) -> T | None:
    ret: list[T] = find(partial(_get_pred, attrs=attrs), iterable, count=1)
    if not ret:
        return None
    return ret[0]


@overload
def get(iterable: Iterable[T], /, **attrs: Any) -> T | None: ...


@overload
async def get(iterable: AsyncIterable[T], /, **attrs: Any) -> T | None: ...


def get(iterable: Iterable[T] | AsyncIterable[T], /, **attrs: Any) -> (T | None) | Coroutine[None, None, T | None]:
    """A shortcut of :func:`find` that passes a predicate that gets attributes from the items in ``iterable``
    and matches them with the attribute names.

    To find sub-attributes, you can use ``__``, so if you want to access ``attribute.sub`` you would pass
    the ``attribute__sub`` keyword.

    If ``iterable`` is an :class:`collections.abc.AsyncIterable`, then this returns a coroutine.
    """
    if isinstance(iterable, AsyncIterable):
        return _aget(iterable, attrs)
    else:
        return _get(iterable, attrs)


def base64_to_bytes(data: str) -> bytes:
    """A shortcut for :meth:`base64.b64decode` with ``data`` being ``ascii`` encoded."""
    return b64decode(data.encode("ascii"))


def get_image_mime_type(data: bytes) -> str:
    """Gets the mime type for an initial image data bytes, in case it is not
    found in the available Discord mime types then this raises a :exc:`ValueError`.
    """

    if data.startswith(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"):
        return "image/png"
    elif data[0:3] == b"\xff\xd8\xff" or data[6:10] in (b"JFIF", b"Exif"):
        return "image/jpeg"
    elif data.startswith((b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")):
        return "image/gif"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    else:
        raise ValueError("unsupported image type")


def get_audio_mime_type(data: bytes) -> str:
    """Gets the mime type for an initial audio data bytes, in case it is not
    found in the available Discord mime types then this raises a :exc:`ValueError`.
    """

    if data.startswith(b"\x49\x44\x33") or data.startswith(b"\xff\xfb"):
        return "audio/mpeg"
    else:
        raise ValueError("unsupported audio type")


def bytes_to_base64(data: bytes, *, audio: bool = False) -> str:
    """Encodes ``data`` in base64 using :meth:`get_image_mime_type` if ``audio``
    is ``False``, else :meth:`get_audio_mime_type` to encode it.
    """
    fmt = "data:{mime};base64,{data}"
    if audio:
        mime = get_audio_mime_type(data)
    else:
        mime = get_image_mime_type(data)
    b64 = b64encode(data).decode("ascii")
    return fmt.format(mime=mime, data=b64)
