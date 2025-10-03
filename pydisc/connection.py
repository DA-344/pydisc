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

from typing import TYPE_CHECKING, Any

from .enums import Status
from .flags import Intents

if TYPE_CHECKING:
    from .activity import Activity
    from .client import Client

__all__ = (
    "ConnectionState",
)


class ConnectionState:
    def __init__(
        self,
        client: Client,
        intents: Intents,
        *,
        activity: Activity | None = None,
        status: Status | None = None,
        **options: Any,
    ) -> None:
        self.client: Client = client
        self.intents: Intents = intents
        self.activity: Activity | None = activity
        self.status: Status | None = status
        self.large_threshold: int = options.get("large_threshold", 250)
        self.chunk_on_startup: bool = options.get("chunk_on_startup", True)
        self.max_heartbeat_timeout: float = options.get("max_heartbeat_timeout", 30.0)

    def has_initial_presence(self) -> bool:
        return self.activity is not None or self.status is not None

    def get_presence_payload(self) -> dict[str, Any]:
        return {
            "status": self.status and self.status.value,
            "game": self.activity and self.activity.to_dict(),
            "since": 0,
            "afk": False,
        }
