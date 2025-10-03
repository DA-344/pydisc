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
import concurrent.futures
import logging
import sys
import threading
import time
import traceback
from typing import TYPE_CHECKING, Any, Self

import aiohttp
import yarl

from pydisc.activity import Activity
from pydisc.utils import _to_json, _from_json
from pydisc.errors import GatewayConnectionClosed, GatewayReconnectNeeded, WebSocketClosure

from .enums import GatewayOPCodes as OPCodes
from .decompressor import Decompressor, ActiveDecompressor

if TYPE_CHECKING:
    from pydisc.events.router import EventRouter
    from pydisc.http import RESTHandler
    from pydisc.cache._types import CacheProtocol
    from pydisc.client import Client
    from pydisc.connection import ConnectionState

_log = logging.getLogger(__name__)

__all__ = (
    "KeepAliveThread",
    "GatewayRatelimiter",
    "DiscordWebSocketPoller",
)


class KeepAliveThread(threading.Thread):
    def __init__(
        self,
        *args: Any,
        ws: DiscordWebSocketPoller,
        interval: float | None = None,
        **kwargs: Any,
    ) -> None:
        daemon: bool = kwargs.pop("daemon", True)
        name: str = kwargs.pop("name", f"websocket-poller-keep-alive:{id(self):#x}")
        super().__init__(*args, daemon=daemon, name=name, **kwargs)

        self.ws: DiscordWebSocketPoller = ws
        self.main_id: int = ws.thread_id
        self.interval: float | None = interval
        self.ack_message: str = "Sent an ACK for keep alive handler with sequence %s"
        self.blocked_message: str = "Heartbeat acks blocked for more than %s seconds"
        self.behind_message: str = "Can't keep up, websocket is %.1f seconds behind"
        self.restarting_message: str = "Client websocket has stopped responding to the gateway. Closing and restarting..."
        self.stop_ev: threading.Event = threading.Event()
        self.last_ack: float = time.perf_counter()
        self.last_send: float = time.perf_counter()
        self.last_recv: float = time.perf_counter()
        self.latency: float = float("inf")
        self.heartbeat_timeout: float = ws.max_heartbeat_timeout

    def run(self) -> None:
        while not self.stop_ev.wait(self.interval):
            if self.last_recv + self.heartbeat_timeout < time.perf_counter():
                _log.warning(
                    self.restarting_message,
                )
                coro = self.ws.close(4000)
                f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)

                try:
                    f.result()
                except Exception as exc:
                    _log.exception(
                        "An exception ocurred while stopping the gateway. Ignoring:",
                        exc_info=exc,
                    )
                except BaseException as exc:
                    _log.debug(
                        "A base exception was raised while stopping the gateway. Debug data:",
                        exc_info=exc,
                    )
                finally:
                    self.stop()
                return

            data = self.get_payload()
            _log.debug(self.ack_message, data["d"])

            coro = self.ws.send_heartbeat(data)
            f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                total = 0
                while True:
                    try:
                        f.result(10)
                        break
                    except concurrent.futures.TimeoutError:
                        total += 10
                        try:
                            frame = sys._current_frames()[self.main_id]
                        except KeyError:
                            msg = self.blocked_message
                        else:
                            stack = "".join(traceback.format_stack(frame))
                            msg = f"{self.blocked_message}\nLoop thread traceback (most recent call last):\n{stack}"
                        _log.warning(msg, total)
            except Exception:
                self.stop()
            else:
                self.last_send = time.perf_counter()

    def get_payload(self) -> dict[str, Any]:
        return {
            "op": OPCodes.heartbeat,
            "d": self.ws.sequence,
        }

    def stop(self) -> None:
        self.stop_ev.set()

    def tick(self) -> None:
        self.last_recv = time.perf_counter()

    def ack(self) -> None:
        ack_time = time.perf_counter()
        self.last_ack = ack_time
        self.latency = ack_time - self.last_send
        if self.latency > 10:
            _log.warning(self.behind_message, self.latency)


class GatewayRatelimiter:
    def __init__(self, count: int = 110, per: float = 60.0) -> None:
        self.max: int = count
        self.remaining: int = count
        self.window: float = 0.0
        self.per: float = per
        self.lock: asyncio.Lock = asyncio.Lock()

    def is_ratelimited(self) -> bool:
        current = time.time()
        if current > self.window + self.per:
            return False
        return self.remaining == 0

    def get_delay(self) -> float:
        current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        return 0.0

    async def block(self) -> None:
        async with self.lock:
            delta = self.get_delay()
            if delta:
                _log.warning("WebSocket is ratelimited, waiting %.2f seconds", delta)
                await asyncio.sleep(delta)


class DiscordWebSocketPoller:

    DEFAULT_GATEWAY_URL = yarl.URL("wss://gateway.discord.gg/")

    if TYPE_CHECKING:
        ws: aiohttp.ClientWebSocketResponse

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        event_router: EventRouter,
        *,
        gateway_url: yarl.URL | None = None,
        compress: bool = True,
        encoding: str = "json",
        rest: RESTHandler,
        initial: bool = False,
        sequence: int | None = None,
        session_id: str | None = None,
    ) -> None:
        self.keep_alive: KeepAliveThread | None = None
        self.loop: asyncio.AbstractEventLoop = loop
        self.gateway_url: yarl.URL = gateway_url or self.DEFAULT_GATEWAY_URL
        self.initial_identify: bool = initial

        self.thread_id: int = threading.get_ident()
        self.event_router: EventRouter = event_router

        self.session_id: str | None = session_id
        self.sequence: int | None = sequence
        self.decompressor: Decompressor = ActiveDecompressor()
        self.close_code: int | None = None
        self.rate_limiter: GatewayRatelimiter = GatewayRatelimiter()
        self.rest_handler: RESTHandler = rest

        from pydisc.http import API_VERSION

        if not compress:
            self.gateway_url = self.gateway_url.with_query(v=API_VERSION, encoding=encoding)
        else:
            self.gateway_url = self.gateway_url.with_query(v=API_VERSION, encoding=encoding, compress=ActiveDecompressor.COMPRESSION_TYPE)

    @property
    def open(self) -> bool:
        return not self.ws.closed

    @property
    def client(self) -> Client:
        return self.event_router.client

    @property
    def cache(self) -> CacheProtocol:
        return self.client.cache

    @property
    def connection(self) -> ConnectionState:
        return self.client._connection

    @property
    def token(self) -> str | None:
        self.rest_handler.token

    @property
    def max_heartbeat_timeout(self) -> float:
        return self.connection.max_heartbeat_timeout

    def is_ratelimited(self) -> bool:
        return self.rate_limiter.is_ratelimited()

    async def start(self, *, resume: bool) -> Self:
        self.ws = await self.rest_handler.session.ws_connect(str(self.gateway_url))

        await self.poll_event()

        if not resume:
            await self.identify()
            return self
        await self.resume()
        return self

    async def send_as_json(self, data: Any) -> None:
        try:
            await self.send(_to_json(data))
        except RuntimeError as exc:
            if not self.can_handle_close_code():
                raise GatewayConnectionClosed(self.ws) from exc

    async def send(self, data: str, /) -> None:
        await self.rate_limiter.block()
        await self.ws.send_str(data)

    async def send_heartbeat(self, data: Any) -> None:
        try:
            await self.ws.send_str(_to_json(data))
        except RuntimeError as exc:
            if not self.can_handle_close_code():
                raise GatewayConnectionClosed(self.ws) from exc

    async def change_voice_state(
        self,
        guild_id: int,
        channel_id: int | None,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        payload: dict[str, Any] = {
            "op": OPCodes.voice_state_update,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": self_mute,
                "self_deaf": self_deaf,
            },
        }

        _log.debug("Sending VOICE_STATE_UPDATE op code with payload %s", payload)
        await self.send_as_json(payload)

    async def change_presence(
        self,
        *,
        activity: Activity | None = None,
        status: str | None = None,
        since: float = 0.0,
    ) -> None:
        if activity is not None:
            if not isinstance(activity, Activity):
                raise TypeError("activity must be an Activity instance")
            activities = [activity.to_dict()]
        else:
            activities = []

        if status == "idle":
            since = int(time.time() * 1000)

        payload: dict[str, Any] = {
            "op": OPCodes.presence_update,
            "d": {
                "activites": activities,
                "afk": False,
                "since": since,
                "status": status,
            },
        }
        await self.send_as_json(payload)

    async def identify(self) -> None:
        payload: dict[str, Any] = {
            "op": OPCodes.identify,
            "d": {
                "token": self.token,
                "properties": {
                    "os": sys.platform,
                    "browser": "pydisc",
                    "device": "pydisc",
                },
                "compress": True,
                "large_threshold": self.connection.large_threshold,
            },
        }

        if self.connection.has_initial_presence():
            payload["d"]["presence"] = self.connection.get_presence_payload()

        if self.connection.intents:
            payload["d"]["intents"] = self.connection.intents.value

        await self.event_router.invoke(event="before_identify", async_invoke=True, args=(self.initial_identify,))
        await self.send_as_json(payload)
        _log.debug("Sent IDENTIFY payload: %s", payload)

    async def resume(self) -> None:
        payload: dict[str, Any] = {
            "op": OPCodes.resume,
            "d": {
                "seq": self.sequence,
                "session_id": self.session_id,
                "token": self.token,
            },
        }
        await self.send_as_json(payload)
        _log.debug("Sent RESUME payload: %s", payload)

    async def close(self, code: int = 4000) -> None:
        if self.keep_alive:
            self.keep_alive.stop()
            self.keep_alive = None
        self.close_code = code
        await self.ws.close(code=code)

    def can_handle_close_code(self) -> bool:
        code = self.close_code or self.ws.close_code
        is_improper = self.close_code is None and self.ws.close_code == 1000
        return is_improper or code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)

    async def received_message(self, msg: Any, /) -> None:
        if type(msg) is bytes:
            msg = self.decompressor.decompress(msg)
            if msg is None:
                return  # a partial message

        msg = _from_json(msg)

        _log.debug("Received WebSocket event: %s", msg)

        event = msg.get("t")
        if event:
            # this is only present when op is 0
            self.event_router.invoke("socket_event_type", async_invoke=False, args=(event,))

        op = msg.get("op")
        data = msg.get("d")
        seq = msg.get("s")

        if seq is not None:
            self.sequence = seq

        if op != OPCodes.dispatch:
            if op == OPCodes.reconnect:
                _log.debug("Received a RECONNECT.")
                await self.close()
                raise GatewayReconnectNeeded
            elif op == OPCodes.heartbeat_ack:
                if self.keep_alive:
                    self.keep_alive.tick()
                return
            elif op == OPCodes.heartbeat:
                if self.keep_alive:
                    beat = self.keep_alive.get_payload()
                    await self.send_as_json(beat)
                return
            elif op == OPCodes.hello:
                interval = data["heartbeat_interval"] / 1000.0
                self.keep_alive = KeepAliveThread(ws=self, interval=interval)
                await self.send_as_json(self.keep_alive.get_payload())
                self.keep_alive.start()
                return
            elif op == OPCodes.invalid_session:
                if data is True:
                    await self.close()
                    raise GatewayReconnectNeeded

                self.sequence = None
                self.session_id = None
                self.gateway_url = self.DEFAULT_GATEWAY_URL
                _log.info("Gateway session has been invalidated, reconnecting...")
                await self.close(code=1000)
                raise GatewayReconnectNeeded

            _log.warning("Not handling unknown OP code %s with data %s", op, data)

        if event == "READY":
            self.sequence = msg["s"]
            self.session_id = data["session_id"]
            self.gateway_url = yarl.URL(data["resume_gateway_url"])
            _log.info("Connected to Gateway (Sequence %d, Session ID %s)", self.sequence, self.session_id)
        elif event == "RESUMED":
            _log.info("Successfully RESUME'd session %s", self.session_id)

        self.event_router.parse_event(event, data)

    @property
    def latency(self) -> float:
        heartbeat = self.keep_alive
        return float("inf") if heartbeat is None else heartbeat.latency

    async def poll_event(self) -> None:
        try:
            msg = await self.ws.receive(timeout=self.max_heartbeat_timeout)
            if msg.type is aiohttp.WSMsgType.TEXT:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.ERROR:
                _log.debug("Received an error wsmsgtype: %s", msg)
                raise WebSocketClosure
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                _log.debug("Receieved a closed message type: %s", msg)
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as exc:
            if self.keep_alive:
                self.keep_alive.stop()
                self.keep_alive = None

            if isinstance(exc, asyncio.TimeoutError):
                _log.debug("Timed out waiting for a websocket message. Attempting a reconnect.")
                raise GatewayReconnectNeeded from None

            code = self.close_code or self.ws.close_code
            if self.can_handle_close_code():
                _log.debug("Websocket closed with a code of %s, attempting a reconnect.", code)
                raise GatewayReconnectNeeded from None
            else:
                _log.debug("Websocket closed with a code of %s.", code)
                raise GatewayConnectionClosed(self.ws, code=code) from None
