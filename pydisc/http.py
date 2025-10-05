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
from collections.abc import Coroutine, Iterable, Sequence
import logging
import sys
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Final, NamedTuple, Self, TypeVar

import aiohttp
from urllib.parse import quote as _uriquote

from .flags import MessageFlags
from .missing import MISSING, MissingOr
from . import utils, __version__
from .file import File
from .embed import Embed
from .ratelimits import RateLimiter
from .errors import DiscordServerError, Forbidden, HTTPException, NotFound, RateLimited

if TYPE_CHECKING:
    from .allowed_mentions import AllowedMentions
    from .attachment import Attachment
    from .components import Component
    from .message import MessageReference
    from .poll import Poll
    from .cache._types import CacheProtocol
    from .abc import Snowflake
    from .channels.forum import ForumTag

    Coro = Coroutine[Any, Any, "T"]

BE = TypeVar("BE", bound=BaseException)
T = TypeVar("T")
_log = logging.getLogger(__name__)

__all__ = (
    "json_or_text",
    "MultipartParameters",
    "handle_message_parameters",
    "Route",
    "RESTHandler",
)


async def json_or_text(response: aiohttp.ClientResponse) -> dict[str, Any] | str:
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            return utils._from_json(text)
    except KeyError:
        pass
    return text


class MultipartParameters(NamedTuple):
    payload: dict[str, Any] | None
    multipart: list[dict[str, Any]] | None
    files: MissingOr[Sequence[File] | None]

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BE] | None,
        exc: BE | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.files:
            for file in self.files:
                file.close()


def handle_message_parameters(
    content: MissingOr[str | None] = MISSING,
    *,
    username: MissingOr[str] = MISSING,
    avatar_url: Any = MISSING,
    tts: bool = False,
    nonce: MissingOr[int | str] = MISSING,
    flags: MissingOr[MessageFlags] = MISSING,
    files: MissingOr[Sequence[File]] = MISSING,
    embeds: MissingOr[Sequence[Embed] | None] = MISSING,
    attachments: MissingOr[Sequence[Attachment | File]] = MISSING,
    components: MissingOr[Sequence[Component] | None] = MISSING,
    allowed_mentions: MissingOr[AllowedMentions] = MISSING,
    reference: MissingOr[MessageReference] = MISSING,
    stickers: MissingOr[Sequence[Snowflake] | None] = MISSING,
    thread_name: MissingOr[str] = MISSING,
    channel_payload: MissingOr[dict[str, Any]] = MISSING,
    applied_tags: MissingOr[Sequence[ForumTag] | None] = MISSING,
    poll: MissingOr[Poll | None] = MISSING,
    cache: CacheProtocol,
    enforce_nonce: MissingOr[bool] = MISSING,
) -> MultipartParameters:
    if attachments is not MISSING and files is not MISSING:
        raise TypeError("can not mix attachments and files keywords")

    payload: dict[str, Any] | None = {}

    if embeds is not MISSING:
        if embeds is None:
            payload["embeds"] = []
        else:
            if len(embeds) > 10:
                raise ValueError("maximum number of embeds exceeded (10)")
            payload["embeds"] = [e.to_dict() for e in embeds]

    if content is not MISSING:
        if content is None:
            payload["content"] = None
        else:
            payload["content"] = content

    if components is not MISSING:
        if components is None:
            payload["components"] = []
        else:
            comps: list[dict[str, Any]] = []
            for comp in components:
                if comp.is_dispatchable():
                    cache.store_component(comp)
                comps.append(comp.to_dict())
            payload["components"] = comps

    if nonce is not MISSING:
        payload["nonce"] = nonce

    if enforce_nonce is not MISSING:
        payload["enforce_nonce"] = enforce_nonce

    if reference is not MISSING:
        payload["message_reference"] = reference.to_dict()

    if stickers is not MISSING:
        if stickers is None:
            payload["sticker_ids"] = []
        else:
            payload["sticker_ids"] = [s.id for s in stickers]

    if tts is not MISSING:
        payload["tts"] = tts

    if avatar_url is not MISSING:
        payload["avatar_url"] = avatar_url

    if username is not MISSING:
        payload["username"] = username

    if flags is not MISSING:
        payload["flags"] = flags.value

    if thread_name is not MISSING:
        payload["thread_name"] = thread_name

    if allowed_mentions is not MISSING:
        payload["allowed_mentions"] = allowed_mentions.to_dict()

    if attachments is MISSING:
        attachments = files
    else:
        files = [a for a in attachments if isinstance(a, File)]

    if attachments is not MISSING:
        idx = 0
        attachments_payload: list[dict[str, Any]] = []
        for attachment in attachments:
            if isinstance(attachment, File):
                attachments_payload.append(attachment.to_dict(idx))
                idx += 1
            else:
                attachments_payload.append(attachment.to_dict())

        payload["attachments"] = attachments_payload

    if applied_tags is not MISSING:
        if applied_tags is None:
            payload["applied_tags"] = []
        else:
            payload["applied_tags"] = [at.id for at in applied_tags]

    if channel_payload is not MISSING:
        payload = {
            "message": payload,
        }
        payload.update(channel_payload)

    if poll is not MISSING:
        if poll is None:
            payload["poll"] = None
        else:
            payload["poll"] = poll.to_dict()

    multipart: list[dict[str, Any]] = []
    if files:
        multipart.append({"name": "payload_json", "value": utils._to_json(payload)})
        payload = None
        for index, file in enumerate(files):
            multipart.append(
                {
                    "name": f"files[{index}]",
                    "value": file.buffer,
                    "filename": file.filename,
                    "content_type": "application/octet-stream",
                },
            )

    return MultipartParameters(payload=payload, multipart=multipart, files=files)


class Route:
    BASE: ClassVar[str] = "https://discord.com/api/v10"

    def __init__(self, method: str, path: str, *, metadata: str | None = None, **parameters: Any) -> None:
        self.path: str = path
        self.method: str = method
        self.metadata: str | None = metadata
        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: _uriquote(v, safe="") if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url

        self.channel_id: str | int | None = parameters.get("channel_id")
        self.guild_id: str | int | None = parameters.get("guild_id")
        self.webhook_id: str | int | None = parameters.get("webhook_id")
        self.webhook_token: str | None = parameters.get("webhook_token")

    @property
    def key(self) -> str:
        if self.metadata:
            return f"{self.method} {self.path}:{self.metadata}"
        return f"{self.method} {self.path}"

    @property
    def major_params(self) -> str:
        return "+".join(
            str(k) for k in (self.channel_id, self.guild_id, self.webhook_id, self.webhook_token) if k is not None
        )


API_VERSION: Final[int] = 10
DISCORD_BASE_URL: Final[str] = f"https://discord.com/api/v{API_VERSION}"


class RESTHandler:
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        base_url: str = DISCORD_BASE_URL,
        *,
        proxy: str | None = None,
        proxy_auth: aiohttp.BasicAuth | None = None,
        connector: aiohttp.BaseConnector | None = None,
        max_ratelimit_timeout: float | None = 30.0,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.base_url: str = base_url
        self.proxy: str | None = proxy
        self.proxy_auth: aiohttp.BasicAuth | None = proxy_auth
        self.connector: aiohttp.BaseConnector | None = connector
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            loop=loop,
            proxy=proxy,
            proxy_auth=proxy_auth,
            connector=connector,
        )
        self._bucket_hashes: dict[str, str] = {}
        self._buckets: dict[str, RateLimiter] = {}
        self._global_rl_over: asyncio.Event = asyncio.Event()
        self._max_rl_timeout: float | None = max_ratelimit_timeout
        user_agent: str = "DiscordBot (https://github.com/DA-344/pydisc) / PyDisc {0} / Python {1} / aiohttp {2}"
        self.user_agent: str = user_agent.format(
            __version__,
            sys.version,
            aiohttp.__version__,
        )
        self.token: str | None = None

    async def close(self) -> None:
        if not self.session.closed:
            await self.session.close()

    def clear(self) -> None:
        if self.session.closed:
            self.session = aiohttp.ClientSession(
                loop=self.loop,
                proxy=self.proxy,
                proxy_auth=self.proxy_auth,
                connector=self.connector,
            )

    @property
    def max_ratelimit_timeout(self) -> float | None:
        return self._max_rl_timeout

    @max_ratelimit_timeout.setter
    def max_ratelimit_timeout(self, value: float | None) -> None:
        for rl in self._buckets.values():
            rl.max_ratelimit_timeout = value
        self._max_rl_timeout = value

    def _get_bucket(self, key: str) -> RateLimiter:
        if key not in self._buckets:
            self._buckets[key] = RateLimiter(5, 1, name=key, max_ratelimit_timeout=self.max_ratelimit_timeout)
        return self._buckets[key]

    async def request(
        self,
        route: Route,
        *,
        files: Sequence[File] | None = None,
        form: Iterable[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Any:
        method = route.method
        url = route.url
        route_key = route.key

        bucket_hash = None

        try:
            bucket_hash = self._bucket_hashes[route_key]
        except KeyError:
            key = f"{route_key}:{route.major_params}"
        else:
            key = f"{bucket_hash}:{route.major_params}"

        ratelimit = self._get_bucket(key)

        headers = kwargs.pop("headers", {})
        headers["User-Agent"] = self.user_agent

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
            kwargs["data"] = utils._to_json(kwargs.pop("json"))

        try:
            reason = kwargs.pop("reason")
        except KeyError:
            pass
        else:
            if reason:
                headers["X-Audit-Log-Reason"] = _uriquote(reason, safe="/ ")

        kwargs["headers"] = headers

        if not self._global_rl_over.is_set():
            # this waits until the global rate limit is raised
            await self._global_rl_over.wait()

        response: aiohttp.ClientResponse | None = None
        data: dict[str, Any] | str | None = None

        async with ratelimit:
            for attempt in range(5):
                if files:
                    for f in files:
                        f.reset(seek=bool(attempt))

                if form:
                    form_data = aiohttp.FormData(quote_fields=False)
                    for params in form:
                        form_data.add_field(**params)
                    kwargs["data"] = form_data

                try:
                    async with self.session.request(method, url, **kwargs) as response:
                        _log.debug("%s %s sent %s returned %s", method, url, kwargs.get("data"), response.status)

                        data = await json_or_text(response)

                        rl_hash = response.headers.get("X-RateLimit-Bucket")
                        has_rl_headers = "X-RateLimit-Remaining" in response.headers
                        if rl_hash is not None:
                            if bucket_hash != rl_hash:
                                if bucket_hash is not None:
                                    _log.debug(
                                        "The route %s has changed bucket hashes: %s -> %s", route_key, bucket_hash, rl_hash
                                    )

                                    self._bucket_hashes[route_key] = rl_hash
                                    self._buckets[f"{rl_hash}:{route.major_params}"] = ratelimit
                                    self._buckets.pop(key, None)
                                elif route_key not in self._bucket_hashes:
                                    _log.debug("Received a new bucket hash for route %s: %s", route_key, rl_hash)
                                    self._bucket_hashes[route_key] = rl_hash
                                    self._buckets[f"{rl_hash}:{route.major_params}"] = ratelimit

                        if has_rl_headers:
                            if response.status != 429:
                                ratelimit.update(response)
                                if ratelimit._remaining == 0:
                                    _log.debug(
                                        "A ratelimit %s has been exhausted, pre-emptively rate limiting...",
                                        rl_hash or route_key,
                                    )

                        if 300 > response.status >= 200:
                            _log.debug("%s %s has received %s", route.method, route.path, data)
                            return data

                        if response.status == 429:
                            if not response.headers.get("Via") or isinstance(data, str):
                                raise HTTPException(response, data)

                            if ratelimit._remaining > 0:
                                _log.debug(
                                    "%s %s received a 429 but had %d remaining requests. THis is a sub-ratelimit.",
                                    route.method,
                                    route.path,
                                    ratelimit._remaining,
                                )

                            retry_after: float = data["retry_after"]
                            if self.max_ratelimit_timeout and retry_after > self.max_ratelimit_timeout:
                                _log.warning(
                                    "We are being rate limited. %s %s returned a 429 status code. Waiting %.2f seconds exceeded the ratelimit timeout threshold.",
                                    route.method,
                                    route.path,
                                    retry_after,
                                )
                                raise RateLimited(retry_after)

                            _log.warning(
                                "We are being rate limited. %s %s returned a 429 status code. Waiting for %.2f seconds.",
                                route.method,
                                route.path,
                                retry_after,
                            )
                            _log.debug(
                                "Rate limit exceeded, with bucket hash %s and %r major params.",
                                bucket_hash,
                                route.major_params,
                            )

                            is_global = data.get("global", False)
                            if is_global:
                                _log.warning("Global rate limit has been hit. Retrying in %.2f seconds.", retry_after)
                                self._global_rl_over.clear()

                            await asyncio.sleep(retry_after)
                            _log.debug("Rate limit has been slept and should be cleared. Retrying request...")

                            if is_global:
                                self._global_rl_over.set()
                                _log.debug("Global rate limit over.")
                            continue

                        if response.status in (500, 502, 503, 524):
                            _log.debug("Recieved a %s status code, retrying request...", response.status)
                            await asyncio.sleep(1 + attempt * 2)
                            continue

                        if response.status == 403:
                            raise Forbidden(response, data)
                        elif response.status == 404:
                            raise NotFound(response, data)
                        elif response.status >= 500:
                            raise DiscordServerError(response, data)
                        else:
                            raise HTTPException(response, data)
                except OSError as exc:
                    if attempt < 4 and exc.errno in (54, 10054):
                        await asyncio.sleep(1 + attempt * 2)
                        continue
                    raise exc

            if response is not None:
                if response.status >= 500:
                    raise DiscordServerError(response, data)
                raise HTTPException(response, data)
            raise RuntimeError("unreachable code")

    # stickers

    def get_sticker(self, sticker_id: int) -> Coro[dict[str, Any]]:
        route = Route(
            "GET",
            "/stickers/{sticker_id}",
            sticker_id=sticker_id,
        )
        return self.request(route)

    def list_sticker_packs(self) -> Coro[list[dict[str, Any]]]:
        route = Route(
            "GET",
            "/sticker-packs",
        )
        return self.request(route)

    def get_sticker_pack(self, pack_id: int) -> Coro[dict[str, Any]]:
        route = Route(
            "GET",
            "/sticker-packs/{pack_id}",
            pack_id=pack_id,
        )
        return self.request(route)

    def list_guild_stickers(self, guild_id: int) -> Coro[list[dict[str, Any]]]:
        route = Route(
            "GET",
            "/guilds/{guild_id}/stickers",
            guild_id=guild_id,
        )
        return self.request(route)

    def get_guild_sticker(self, guild_id: int, sticker_id: int) -> Coro[dict[str, Any]]:
        route = Route(
            "GET",
            "/guilds/{guild_id}/stickers/{sticker_id}",
            guild_id=guild_id,
            sticker_id=sticker_id,
        )
        return self.request(route)

    def create_guild_sticker(
        self,
        guild_id: int,
        *,
        payload: dict[str, Any],
        file: File,
        reason: str | None,
    ) -> Coro[dict[str, Any]]:
        initial_bytes = file.buffer.read(16)

        try:
            mime_type = utils.get_image_mime_type(initial_bytes)
        except ValueError:
            if initial_bytes.startswith(b"{"):
                mime_type = "application/json"
            else:
                mime_type = "application/octet-stream"
        finally:
            file.reset()

        form: list[dict[str, Any]] = [
            {
                "name": "file",
                "value": file.buffer,
                "filename": file.filename,
                "content_type": mime_type,
            },
        ]

        for k, v in payload.items():
            form.append(
                {
                    "name": k,
                    "value": v,
                },
            )

        route = Route(
            "POST",
            "/guilds/{guild_id}/stickers",
            guild_id=guild_id,
        )
        return self.request(route, form=form, files=[file], reason=reason)
