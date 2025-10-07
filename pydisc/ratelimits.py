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
import time
from collections import deque
from typing import Any, Self

import aiohttp

from .errors import RateLimited

_log = logging.getLogger(__name__)

__all__ = ("RateLimiter",)


class RateLimiter:
    def __init__(
        self,
        limit: int,
        period: float,
        name: str,
        max_ratelimit_timeout: float | None = None,
    ) -> None:
        self.name: str = name
        self.limit: int = limit
        self.period: float = period
        self.max_ratelimit_timeout: float | None = max_ratelimit_timeout

        self._queue: deque[asyncio.Future] = deque()
        self._remaining: int = limit
        self._window_reset: float = time.monotonic() + period
        self._throttle_task: asyncio.Task | None = None

        self._global_reset: float | None = None

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def acquire(self) -> None:
        now = time.monotonic()
        self._refresh_window(now)

        if self._global_reset is not None:
            wait_time = self._global_reset - now
            if wait_time > 0:
                await self._handle_wait(wait_time)

        if self._remaining > 0:
            self._remaining -= 1
            return

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._queue.append(fut)

        if self._throttle_task is None:
            self._throttle_task = loop.create_task(self._process_queue())
        await fut

    def _refresh_window(self, now: float) -> None:
        if now >= self._window_reset:
            self._remaining = self.limit
            self._window_reset = now + self.period

    async def _process_queue(self) -> None:
        while self._queue:
            now = time.monotonic()
            self._refresh_window(now)

            wait_time = max(0, self._window_reset - now)
            if self._remaining == 0:
                await self._handle_wait(wait_time)
                continue

            while self._remaining > 0 and self._queue:
                self._remaining -= 1
                fut = self._queue.popleft()
                fut.set_result(None)

        self._throttle_task = None

    async def _handle_wait(self, wait_time: float) -> None:
        if self.max_ratelimit_timeout is not None and wait_time > self.max_ratelimit_timeout:
            while self._queue:
                fut = self._queue.popleft()
                fut.set_exception(RateLimited(wait_time))
            raise RateLimited(wait_time)

        _log.debug("Bucket %s sleeping for %.2f seconds", self.name, wait_time)
        await asyncio.sleep(wait_time)

    def set_global_ratelimit(self, retry_after: float) -> None:
        self._global_reset = time.monotonic() + retry_after
        _log.warning("We are being globally ratelimited in bucket %s, sleeping %.2f", self.name, retry_after)

    def update(self, request: aiohttp.ClientResponse) -> None:
        limit = self.limit
        remaining = self._remaining

        if rl_limit_header := request.headers.get("X-RateLimit-Limit"):
            limit = int(rl_limit_header)

        if rl_rem_header := request.headers.get("X-RateLimit-Remaining"):
            remaining = int(rl_rem_header)

        self._remaining = remaining
        self.limit = limit

        # i prefer this header because it returns rounded numbers
        if rl_reset_after := request.headers.get("X-RateLimit-Reset-After"):
            self._window_reset = time.monotonic() + float(rl_reset_after)
