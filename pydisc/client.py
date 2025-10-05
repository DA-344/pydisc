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
import logging
from typing import Any, Generic
from typing_extensions import TypeVar

import aiohttp

from .errors import GatewayConnectionClosed, GatewayReconnectNeeded, HTTPException, PriviligedIntentsRequired
from .backoff import ExponentialBackoff
from .flags import Intents
from .http import RESTHandler
from .connection import ConnectionState
from .cache import DefaultCache, CacheProtocol
from .websockets import DiscordWebSocketPoller
from .events import EventRouter
from .missing import MissingOr, MISSING
from .user import ClientUser
from .message import Message

C = TypeVar("C", bound=CacheProtocol, covariant=True, default=DefaultCache)
_log = logging.getLogger(__name__)

__all__ = ("Client",)


class _Loop:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        raise AttributeError(
            "loop must be used in async contexts. If you want to use a loop in a non-async "
            "context then you should create one manually and use it, or use the provided async_setup "
            "overrideable function in Client to do your async operations.",
        )

_loop: Any = _Loop()


class Client(Generic[C]):
    """Represents a Client that can be connected to Discord.

    This supports using ``async with client`` syntax to automatically clean up the
    Client after it's usage.

    Parameters
    ----------
    intents: :class:`Intents`
        The intents to use for the client initialize.
    proxy: :class:`str`
        The proxy URL to use for this client.
    proxy_auth: :class:`aiohttp.BasicAuth`
        The auth to use for the proxy.
    loop: :class:`asyncio.AbstractEventLoop`
        The loop to use for this client.
    activity: :class:`Activity`
        The activity to start the bot with when starting the Gateway connection.
    status: :class:`Status`
        The status to set the bot into when starting the Gateway connection.
    large_threshold: :class:`int`
        The amount of members in a guild required for it to be considered as large.
        You can check whether a guild is considered large with :attr:`Guild.large`.
        Defaults to ``250``.
    chunk_on_startup: :class:`bool`
        Whether the bot guilds should be chunked on startup so the members are cached.
    max_heartbeat_timeout: :class:`float`
        The maximum latency allowed for Gateway heartbeats before considering it as timedout.
    max_ratelimit_timeout: :class:`float` | :data:`None`
        The maximum amount of seconds allowed for a ratelimit retry after to be, if it exceeds
        this threshold, then :exc:`RateLimited` is raised. If this is :data:`None` then it is
        considered as there should be no timeout and all retry afters should be waited for.
    connector: :class:`aiohttp.BaseConnector`
        The connector to use for the client http requests. This can be used to control underlying
        aiohttp behavior, such as setting a DNS resolver os SSL context.
    cache_cls: type[:class:`~pydisc.cache.CacheProtocol`]
        A CacheProtocol subclass used to create this client's cache. Defaults to :class:`pydisc.cache.DefaultCache`.
    """

    def __init__(
        self,
        *,
        intents: Intents,
        cache_cls: type[C] = CacheProtocol,
        **options: Any,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = _loop
        """The loop used for this client asynchronous operations."""
        self.http: RESTHandler = RESTHandler(
            self.loop,
            **options,
        )
        self._connection: ConnectionState = ConnectionState(
            self,
            intents,
            **options,
        )
        self.events: EventRouter = EventRouter(self)
        """The event router that allows you to register event listeners."""
        self.cache: C = cache_cls(self)
        """The cache object that allows you to handle your cache."""
        self._ws: DiscordWebSocketPoller = DiscordWebSocketPoller(
            self.loop,
            self.events,
            rest=self.http,
            initial=True,
        )
        self._closing_task: asyncio.Task[Any] | None = None
        self._ready: MissingOr[asyncio.Event] = MISSING
        self.user: ClientUser | None = None
        """The user attached to this client. This is filled once after :meth:`login` is called."""

    def is_closed(self) -> bool:
        """Whether the client has closed it's websocket connection, or is currently closing it."""
        return self._closing_task is not None

    @property
    def intents(self) -> Intents:
        """The intents used for the client Gateway connection."""
        # intents should not be runtime-modifyable, so return a copy
        return Intents(self._connection.intents.value)

    @property
    def latency(self) -> float:
        """Returns the latency of this client in seconds.

        This may return ``float("inf")`` if the websocket is not yet
        ready, or ``float("nan")`` if there is no websocket connection.
        """
        if not self._ws.has_started():
            return float("nan")
        return self._ws.latency

    @property
    def proxy(self) -> str | None:
        """The proxy of this client for HTTP requests."""
        return self.http.proxy

    @property
    def proxy_auth(self) -> aiohttp.BasicAuth | None:
        """The proxy authorization of this client for HTTP requests."""
        return self.http.proxy_auth

    async def connect(self, *, reconnect: bool = True) -> None:
        """Starts the websocket connection to the Discord Gateway.

        Parameters
        ----------
        reconnect: :class:`bool`
            Whether reconnecting should be attempted.
        """

        backoff = ExponentialBackoff()
        resume: bool = False

        while not self.is_closed():
            try:
                await asyncio.wait_for(self._ws.start(resume=resume), timeout=60.0)
                self._ws.update(initial=False)
                while True:
                    await self._ws.poll_event()
            except GatewayReconnectNeeded as exc:
                _log.debug("Websocket asks for a reconnect when receiving an OP code of %s", exc)
                self.events.invoke("disconnect")
                resume = exc.resume
                continue
            except (
                OSError,
                HTTPException,
                GatewayConnectionClosed,
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:
                self.events.invoke("disconnect")
                if not reconnect:
                    await self.close()
                    if isinstance(exc, GatewayConnectionClosed) and exc.code == 1000:
                        return
                    raise

                if self.is_closed():
                    return

                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    self._ws.update(
                        initial=False,
                    )
                    resume = True
                    continue

                if isinstance(exc, GatewayConnectionClosed):
                    if exc.code == 4014:
                        raise PriviligedIntentsRequired from None
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("An error ocurred while connecting to the websocket, attempting a reconnect in %.2f", retry)
                await asyncio.sleep(retry)
                resume = True
                continue

    async def close(self) -> None:
        """Closes the connection to Discord."""

        if self._closing_task is not None:
            return await self._closing_task

        async def _close():
            if self._ws.open:
                await self._ws.close(code=1000)
            await self.http.close()
            if self._ready is not MISSING:
                self._ready.clear()
            self.loop = _loop

        self._closing_task = asyncio.create_task(_close())
        await self._closing_task

    def clear(self) -> None:
        """Clears the internal state of the bot."""
        if self._ready is not MISSING:
            self._ready.clear()
        self._closing_task = None
        self.http.clear()

    def _create_message_(self, data: dict[str, Any]) -> Message:
        return Message(data, self.cache)
