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

import asyncio
from collections.abc import Callable, Coroutine
import logging
from typing import TYPE_CHECKING, Any, Literal, TypeVar, overload

from .models import (
    EventModel,
    InteractionCreate,
)

if TYPE_CHECKING:
    from pydisc.client import Client
    from pydisc.connection import ConnectionState
    from pydisc.cache._types import CacheProtocol

T = TypeVar("T")
Coro = Callable[..., Coroutine[Any, Any, T]]
_log = logging.getLogger(__name__)

__all__ = (
    "EventRouter",
)


class EventRouter:
    """Represents an event emitter for a :class:`Client`.

    This may be overriden to add custom behaviour or event dispatching.
    """

    def __init__(self, client: Client[Any]) -> None:
        self.client: Client[Any] = client
        self.task_set: set[asyncio.Task[Any]] = set()
        self._events: dict[str, list[Coro[Any]]] = {}
        self._waiters: dict[str, list[asyncio.Future[Any]]] = {}

    @property
    def _connection(self) -> ConnectionState:
        return self.client._connection

    @property
    def cache(self) -> CacheProtocol:
        return self.client.cache

    async def _invoke(self, coros: list[Coro[Any]], args: Any, kwargs: dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        tasks = [loop.create_task(coro(*args, **kwargs)) for coro in coros]
        await asyncio.gather(*tasks)

    @overload
    async def invoke(
        self,
        event: str,
        *,
        async_invoke: Literal[True],
        args: Any | None = ...,
        kwargs: dict[str, Any] | None = ...,
    ) -> None: ...

    @overload
    def invoke(
        self,
        event: str,
        *,
        async_invoke: Literal[False] = ...,
        args: Any | None = ...,
        kwargs: dict[str, Any] | None = ...,
    ) -> None: ...

    def invoke(
        self,
        event: str,
        *,
        async_invoke: bool = False,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None | Coroutine[None, None, None]:
        """Invokes an event with the provided args and kwargs.

        If ``async_invoke`` is ``True``, then this returns a coroutine that must be awaited
        in order for the dispatch to be completed.
        """
        coros = self._events.get(event, [])
        loop = asyncio.get_running_loop()
        args = args or ()
        kwargs = kwargs or {}

        _log.debug("Invoking event %s (locked: %s) with args %s and kwargs %s", event, async_invoke, args, kwargs)

        if async_invoke is True:
            return self._invoke(coros, args, kwargs)

        for coro in coros:
            task = asyncio.ensure_future(
                coro(*args, **kwargs),
                loop=loop,
            )
            self.task_set.add(task)
            task.add_done_callback(self.task_set.discard)

    @overload
    async def parse_event(
        self,
        event: str,
        data: dict[str, Any],
        *,
        async_invoke: Literal[True],
    ) -> None: ...

    @overload
    def parse_event(
        self,
        event: str,
        data: dict[str, Any],
        *,
        async_invoke: Literal[False] = ...,
    ) -> None: ...

    def parse_event(
        self,
        event: str,
        data: dict[str, Any],
        *,
        async_invoke: bool = False,
    ) -> None | Coroutine[None, None, None]:
        """Parses an event received via the Discord WebSocket."""
        event = event.lower()

        try:
            parser: Callable[[dict[str, Any], ConnectionState], EventModel] = getattr(self, f"parse_{event}")
        except AttributeError:
            _log.warning(
                "Could not parse event %s with data %s. This is a library bug, consider opening "
                "an issue at https://github.com/DA-344/pydisc/issues",
                event,
                data,
            )
            return

        parsed = parser(data, self._connection)

        for fut in self._waiters.get(event, []):
            fut.set_result(None)
        self._waiters.pop(event, None)

        if async_invoke is True:
            return self._parse_event(event, parsed)

        loop = asyncio.get_running_loop()
        task = asyncio.ensure_future(
            self._parse_event(event, parsed),
            loop=loop,
        )
        self.task_set.add(task)
        task.add_done_callback(self.task_set.discard)

    async def handle_interaction(self, payload: InteractionCreate) -> None:
        ...

    async def _parse_event(self, event: str, model: EventModel) -> None:
        model = await model.async_setup()

        # interactions need a special handling for components, modals, slash
        # commands and such things
        if isinstance(model, InteractionCreate):
            await self.handle_interaction(model)
        await self.invoke(
            event,
            async_invoke=True,
            args=(model,),
        )
