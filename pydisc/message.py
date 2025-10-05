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

from collections.abc import Sequence
import datetime
from typing import TYPE_CHECKING, Any, Self
from typing_extensions import deprecated

from .abc import Channel, Snowflake
from .user import User
from .role import Role
from .channels import PartialChannel, Thread
from .channels.factory import channel_factory
from .attachment import Attachment
from .embed import Embed
from .reaction import Reaction
from .application_info import ApplicationInfo
from .components import _pd_to_component, Component
from .sticker import Sticker, StickerItem
from .poll import Poll
from .mixins import Hashable
from .utils import _get_snowflake, parse_time
from .missing import MissingOr, MISSING
from .file import File
from .object import Object
from .flags import MessageFlags
from .http import handle_message_parameters
from .allowed_mentions import AllowedMentions
from .enums import InteractionType, MessageActivityType, MessageReferenceType, MessageType, try_enum
from .member import Member, PartialMember

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .guild import Guild


class PartialMessage(Hashable):
    """Represents a partial message."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The ID of this message."""
        self.channel_id: int = int(data["channel_id"])
        """The channel ID this message was sent to."""
        self.guild_id: int | None = _get_snowflake("guild_id", data)
        """The guild ID this message was sent to."""

    @property
    def channel(self) -> Channel | None:
        """Returns the cached channel this message is from."""
        return self._cache.get_channel(self.channel_id)

    @property
    def guild(self) -> Guild | None:
        """Returns the cached guild this message is from."""
        if self.channel:
            return self.channel.guild
        return self._cache.get_guild(self.guild_id)

    async def edit(
        self,
        *,
        content: MissingOr[str | None] = MISSING,
        embeds: MissingOr[Sequence[Embed] | None] = MISSING,
        suppress_embeds: MissingOr[bool] = MISSING,
        components: MissingOr[Sequence[Component] | None] = MISSING,
        attachments: MissingOr[Sequence[Attachment | File] | None] = MISSING,
        silent: MissingOr[bool] = MISSING,
        allowed_mentions: MissingOr[AllowedMentions] = MISSING,
    ) -> Message:
        """Edits this message. This can only be done by the message author and if it has permissions to
        view the respective channel.
        """

        channel = self.channel or Object(id=self.channel_id)
        cache = self._cache
        client = cache.client
        http = client.http

        flags = MessageFlags(0)

        if suppress_embeds:
            flags |= MessageFlags.suppress_embeds
        if silent:
            flags |= MessageFlags.suppress_notifications
        if any(c.is_v2() for c in (components or [])):
            flags |= MessageFlags.components_v2

        with handle_message_parameters(
            content=content,
            embeds=embeds,
            attachments=attachments or MISSING,
            allowed_mentions=allowed_mentions,
            components=components,
            cache=self._cache,
        ) as params:
            data = await http.edit_message(self.id, channel.id, params=params)

        if cached := cache.get_message(self.id):
            cached.__init__(data, cache)
            return cached

        ret = Message(data, self._cache)
        cache.store_message(ret)
        return ret

    async def reply(
        self,
        content: MissingOr[str] = MISSING,
        *,
        tts: bool = False,
        embeds: MissingOr[Sequence[Embed]] = MISSING,
        files: MissingOr[Sequence[File]] = MISSING,
        stickers: MissingOr[Sequence[Snowflake]] = MISSING,
        nonce: MissingOr[int | str] = MISSING,
        allowed_mentions: MissingOr[AllowedMentions] = MISSING,
        components: MissingOr[Sequence[Component]] = MISSING,
        suppress_embeds: MissingOr[bool] = MISSING,
        enforce_nonce: MissingOr[bool] = MISSING,
        poll: MissingOr[Poll] = MISSING,
        silent: MissingOr[bool] = MISSING,
    ) -> Message:
        """A shortcut for :meth:`Messageable.send` passing ``reference`` as this message."""

        channel = self.channel or Object(id=self.channel_id)
        cache = self._cache
        client = cache.client
        http = client.http

        flags = MessageFlags(0)

        if suppress_embeds:
            flags |= MessageFlags.suppress_embeds
        if silent:
            flags |= MessageFlags.suppress_notifications
        if any(c.is_v2() for c in (components or [])):
            flags |= MessageFlags.components_v2

        with handle_message_parameters(
            content=content,
            tts=tts,
            embeds=embeds,
            files=files,
            stickers=stickers,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=self.to_reference(),
            components=components,
            flags=flags,
            poll=poll,
            enforce_nonce=enforce_nonce,
            cache=self._cache,
        ) as params:
            data = await http.send_message(channel.id, params=params)

        if cached := cache.get_message(self.id):
            cached.__init__(data, cache)
            return cached

        ret = Message(data, self._cache)
        cache.store_message(ret)
        return ret

    def is_reference(self) -> bool:
        """Whether this message is a reference to another message, used for replying to messages
        in :meth:`send` -like methods.
        """
        return False

    def to_reference(
        self,
        *,
        type: MessageReferenceType = MessageReferenceType.default,
        fail_if_not_exists: bool = True,
    ) -> MessageReference:
        """Converts this message into a MessageReference to be passed in :meth:`send` -like methods
        in order to reply to it.
        """
        return MessageReference(
            {
                "id": self.id,
                "channel_id": self.channel_id,
                "guild_id": self.guild_id,
                "type": type.value,
                "fail_if_not_exists": fail_if_not_exists,
            },
            self._cache,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol) -> Self | None:
        if data is None:
            return None
        return cls(data, cache)


class MessageReference(PartialMessage):
    """Represents a reference to a message.

    This inherits from :class:`PartialMessage`, and can be performed
    the same operations as long the current user is in the guild and channel the reference
    points to.
    """

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)
        self.type: MessageReferenceType = try_enum(MessageReferenceType, data.get("type", 0))
        """The type of message reference."""
        self.fail_if_not_exists: bool = data.get("fail_if_not_exists", True)
        """Whether message requests should fail if the referenced message no longer exists."""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "message_id": self.id,
            "channel_id": self.channel_id,
            "type": self.type.value,
            "fail_if_not_exists": self.fail_if_not_exists,
        }
        if self.guild_id is not None:
            payload["guild_id"] = self.guild_id
        return payload

    def to_reference(
        self,
        *,
        type: MessageReferenceType = MessageReferenceType.default,
        fail_if_not_exists: bool = True,
    ) -> MessageReference:
        data = self.to_dict()
        data["type"] = type.value
        data["fail_if_not_exists"] = fail_if_not_exists

        return MessageReference(
            data,
            self._cache,
        )

    def is_reference(self) -> bool:
        return True


class Message(PartialMessage):
    """Represents a message object."""

    if TYPE_CHECKING:
        @deprecated("Message.interaction is deprecated in favor of Message.interaction_metadata")
        @property
        def interaction(self) -> MessageInteraction | None:
            """The interaction data bound to this message.

            This attribute is deprecated, consider using :attr:`interaction_metadata`.
            """
            return NotImplemented

        @deprecated("Message.stickers is deprecated in favor of Message.sticker_items")
        @property
        def stickers(self) -> list[Sticker]:
            """The stickers of this message.

            This attribute is deprecated, consider using :attr:`sticker_items` instead.
            """
            return NotImplemented

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        super().__init__(data, cache)

        self.author: User = User(data["user"], cache)
        """The author of this message. This may point to an invalid user, check :meth:`is_webhook`."""
        self.content: str = data["content"]
        """The contents of this message."""
        self.created_at: datetime.datetime = parse_time(data["timestamp"])
        """When this message was created."""
        self.edited_at: datetime.datetime | None = parse_time(data.get("edited_timestamp"))
        """When this message has been edited, if applicable."""
        self.tts: bool = data.get("tts", False)
        """Whether this message is TTS."""
        self.mention_everyone: bool = data.get("mention_everyone", False)
        """Whether this message mentions ``@everyone``."""
        self._user_mentions: dict[int, User] = {
            int(d["id"]): User(d, cache)
            for d in data.get("mentions", [])
        }
        self._channel_mentions: dict[int, Channel] = {
            int(d["id"]): channel_factory(d, cache)
            for d in data.get("mention_channels", [])
        }
        self._role_mentions: dict[int, Role] = {
            int(d["id"]): Role(d, cache)
            for d in data.get("mention_roles", [])
        }
        self.attachments: list[Attachment] = [Attachment(a, cache) for a in data.get("attachments", [])]
        """The attachments of this message."""
        self.embeds: list[Embed] = [Embed.from_dict(e) for e in data.get("embeds", [])]
        """The embeds of this message."""
        self.reactions: list[Reaction] = Reaction.from_dict_array(data.get("reactions"), cache, self)
        """The reactions of this message."""
        self.nonce: int | str | None = data.get("nonce")
        """The nonce used for validating this message."""
        self.pinned: bool = data.get("pinned", False)
        """Whether this message is pinned."""
        self.webhook_id: int | None = _get_snowflake("webhook_id", data)
        """The webhook ID author of this message, if applicable."""
        self.type: MessageType = try_enum(MessageType, data["type"])
        """The type of this message."""
        self.activity: MessageActivity | None = MessageActivity.from_dict(data.get("activity"))
        """The activity of this message."""
        self.application: ApplicationInfo | None = ApplicationInfo.from_dict(data.get("application"), cache)
        """A partial application object related to :attr:`activity`."""
        self.application_id: int | None = _get_snowflake("application_id", data)
        """For interaction-bound messages (responses and followups), this represents the ID of the application."""
        self._flags: int = data.get("flags", 0)
        self.message_reference: MessageReference | None = MessageReference.from_dict(data.get("message_reference"), cache)
        """The referenced message. This may be applicable for crossposts, channel follow adds, pins, or replies."""
        self.message_snapshots: list[MessageSnapshot] = MessageSnapshot.from_dict_array(data.get("message_snapshots"), cache, self.message_reference)
        """The snapshots of this message. This is only applicable when :attr:`message_reference` is not :data:`None` and
        :attr:`Message.message_reference.type <MessageReference.type>` is :attr:`MessageReferenceType.forward`.
        """
        self.referenced_message: Message | None = Message.from_dict(data.get("referenced_message"), cache)
        """The resolved referenced message. This is only applicable when :attr:`message_reference` is not :data:`None` and
        :attr:`Message.message_reference.type <MessageReference.type>` is :attr:`MessageReferenceType.default`.
        """
        self.interaction_metadata: MessageInteractionMetadata | None = MessageInteractionMetadata.from_dict(
            data.get("interaction_metadata"),
            cache,
            self,
        )
        """The interaction metadata bound to this message."""

        thread: dict[str, Any] | None = data.get("thread")
        self.thread: Thread | None = cache.get_thread(_get_snowflake("id", thread or {}))
        """The thread this message was sent to."""

        if self.thread is None:
            self.thread = Thread.from_dict(thread, cache)
            cache.store_thread(self.thread)
        else:
            if thread:
                self.thread.__init__(thread, cache)

        self.components: list[Component] = [_pd_to_component(c, cache) for c in data.get("components", [])]
        """The components of this message.

        This does not include subclasses nor callbacks.
        """
        self.sticker_items: list[StickerItem] = [StickerItem(s, cache) for s in data.get("sticker_items", [])]
        """The sticker items of this message."""
        self.position: int | None = data.get("position")
        """The estimated position of this message in its :attr:`thread`."""
        self.role_subscription_data: RoleSubscriptionData | None = RoleSubscriptionData.from_dict(data.get("role_subscription_data"))
        """The role subscription data of this message. This is only applicable when :attr:`type` is
        :attr:`MessageType.role_subscription_purchase`.
        """
        self._resolved: ResolvedData = ResolvedData()

        # i don't really like this solution but if we don't do this then
        # the deprecation notices wouldn't make effect and no warnings would
        # be emitted by type checkers
        # should still document it here just to make sure docs are rendered anyways
        if TYPE_CHECKING:
            pass
        else:
            self.interaction: MessageInteraction | None = MessageInteraction.from_dict(data.get("interaction"), cache)
            """The interaction data bound to this message.

            This attribute is deprecated, consider using :attr:`interaction_metadata`.
            """
            self.stickers: list[Sticker] = [Sticker(s, cache) for s in data.get("stickers", [])]
            """The stickers of this message.

            This attribute is deprecated, consider using :attr:`sticker_items` instead.
            """

    @property
    def flags(self) -> MessageFlags:
        """The flags of this message."""
        return MessageFlags(self._flags)


# I'd really like to follow the API structure here, but only if
# PartialMessage implemented the fields message snaphosts provide
# in a consistent way with the other partial messages objects.
class MessageSnapshot(PartialMessage):
    """Represents the snapshot of a message."""

    if TYPE_CHECKING:
        @deprecated("MessageSnapshot.stickers is deprecated in favor of MessageSnapshot.sticker_items")
        @property
        def stickers(self) -> list[Sticker]:
            """The stickers of this message.

            This attribute is deprecated, consider using :attr:`sticker_items` instead.
            """
            return NotImplemented

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, reference: MessageReference) -> None:
        msg = data["message"]

        super().__init__(
            {
                "id": reference.id,
                "channel_id": reference.channel_id,
                "guild_id": reference.guild_id,
            },
            cache,
        )

        self._ref: MessageReference = reference
        self._cache: CacheProtocol = cache
        self.type: MessageType = try_enum(MessageType, msg["type"])
        """The type of this message."""
        self.content: str = data["content"]
        """The contents of this message."""
        self.embeds: list[Embed] = [Embed.from_dict(e) for e in data.get("embeds", [])]
        """The embeds of this message."""
        self.attachments: list[Attachment] = [Attachment(a, cache) for a in data.get("attachments", [])]
        """The attachments of this message."""
        self.created_at: datetime.datetime = parse_time(data["timestamp"])
        """When this message was created."""
        self.edited_at: datetime.datetime | None = parse_time(data.get("edited_timestamp"))
        """When this message has been edited, if applicable."""
        self._flags: int = data.get("flags", 0)
        self._user_mentions: dict[int, User] = {
            int(d["id"]): User(d, cache)
            for d in data.get("mentions", [])
        }
        self._channel_mentions: dict[int, Channel] = {
            int(d["id"]): channel_factory(d, cache)
            for d in data.get("mention_channels", [])
        }
        self._role_mentions: dict[int, Role] = {
            int(d["id"]): Role(d, cache)
            for d in data.get("mention_roles", [])
        }
        self.sticker_items: list[StickerItem] = [StickerItem(d, cache) for d in data.get("sticker_items", [])]
        """The sticker items of this message."""
        self.components: list[Component] = [_pd_to_component(c, cache) for c in data.get("components", [])]
        """The components of this message.

        This does not include subclasses nor callbacks.
        """

        if TYPE_CHECKING:
            pass
        else:
            self.stickers: list[Sticker] = Sticker.from_dict_array(data.get("stickers"), cache)
            """The stickers of this message.

            This attribute is deprecated, consider using :attr:`sticker_items` instead.
            """

    @property
    def guild(self) -> Guild | None:
        """The guild this message was sent to."""
        if self.channel:
            return self.channel.guild
        return None

    @property
    def guild_id(self) -> int | None:
        """The guild ID this message was sent to."""
        if self.guild:
            return self.guild.id
        return None

    @classmethod
    def from_dict_array(cls, data: list[dict[str, Any]] | None, cache: CacheProtocol, reference: MessageReference) -> list[MessageSnapshot]:
        if not data:
            return []
        return [MessageSnapshot(d, cache, reference) for d in data]


class MessageInteractionMetadata(Hashable):
    """Represents the metadata information of an interaction."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol, message: Message) -> None:
        self._message: Message = message
        self._cache: CacheProtocol = cache
        self.id: int = int(data["id"])
        """The ID of the interaction."""
        self.type: InteractionType = try_enum(InteractionType, data["type"])
        """The interaction type."""

        self.user: User = User(data["user"], cache)
        """The user that triggered the interaction."""
        if cached_user := cache.get_user(self.user.id):
            self.user = cached_user
            self.user.__init__(data["user"], cache)

        self._integration_owners: dict[int, int] = {
            int(k): int(v)
            for k, v in
            data.get("authorizing_integration_owners", {}).items()
        }
        self.original_response_id: int | None = _get_snowflake("original_response_id", data)
        """The ID of the original response message."""
        self.interacted_message_id: int | None = _get_snowflake("interaction_message_id", data)
        """The ID of the message that contained the interactive component. In case :attr:`type`
        is :attr:`InteractionType.component`.
        """

        target_user: dict[str, Any] | None = data.get("target_user")
        self.target_user: User | None = cache.get_user(_get_snowflake("id", target_user or {}))
        """The user the command was executed on. In case :attr:`type` is :attr:`InteractionType.command`
        and the command is a user context menu.
        """
        if self.target_user is None:
            self.target_user = User.from_dict(target_user, cache)
            if self.target_user:
                cache.store_user(self.target_user)
        else:
            if target_user:
                self.target_user.__init__(target_user, cache)

        self.target_message_id: int | None = _get_snowflake("target_message_id", data)
        """The message ID the command was executed on. In case :attr:`type` is :attr:`InteractionType.command`
        and the command is a message context menu.
        """
        self.trigger_interaction_metadata: MessageInteractionMetadata | None = MessageInteractionMetadata.from_dict(
            data.get("triggering_interaction_metadata"),
            cache,
            message,
        )
        """The metadata of the interaction that was used to invoke this. In case :attr:`type`
        is :attr:`InteractionType.modal`.
        """

    @property
    def original_response(self) -> Message | None:
        """Returns the cached version of :attr:`original_response_id`."""
        return self._cache.get_message(self.original_response_id)

    @property
    def interacted_message(self) -> Message | None:
        """Returns the cached version of :attr:`interacted_message_id`."""
        return self._cache.get_message(self.interacted_message_id)

    @property
    def target_message(self) -> Message | None:
        """Returns the cached version of :attr:`target_message_id`."""
        return self._cache.get_message(self.target_message_id)

    def is_guild_integration(self) -> bool:
        """Returns whether this interaction is from a guild integration."""
        if self._message.guild_id is not None:
            return self._integration_owners.get(0) == self._message.guild_id
        return False

    def is_user_integration(self) -> bool:
        """Returns whether this interaction is from a user integration."""
        return self._integration_owners.get(1) == self.user.id

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, cache: CacheProtocol, message: Message) -> MessageInteractionMetadata | None:
        if data is None:
            return None
        return MessageInteractionMetadata(data, cache, message)


@deprecated(
    "MessageInteraction is deprecated in favor of MessageInteractionMetadata and will be removed "
    "in the next Discord API version.",
)
class MessageInteraction(Hashable):
    """Represents the interaction data for a message.

    This is deprecated in favor of :attr:`Message.interaction_metadata`.
    """

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.id: int = int(data["id"])
        """The ID of the interaction."""
        self.type: InteractionType = try_enum(InteractionType, data["type"])
        """The type of interaction."""
        self.name: str = data["name"]
        """The name of the invoked command, including subcommands and subcommand groups."""

        user: dict[str, Any] = data["user"]
        self.user: User = User(user, cache)
        """The user that invoked the interaction."""

        if cached_user := cache.get_user(self.user.id):
            self.user = cached_user
            self.user.__init__(user, cache)

        member: dict[str, Any] | None = data.get("member")
        self.member: PartialMember | None = cache.get_member(_get_snowflake("id", member or {}))
        """The member data that invoked the interaction, if in a guild context."""

        if self.member is None:
            self.member = PartialMember.from_dict(member, cache)
        else:
            if member:
                self.member.__init__(member, cache)


class MessageActivity:
    """Represents an activity attached to a message."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.type: MessageActivityType = try_enum(MessageActivityType, data["type"])
        """The type of a message activity."""
        self.party_id: str | None = data.get("party_id")
        """The id of a Rich Presence event invitation."""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MessageActivity | None:
        if data is None:
            return None
        return MessageActivity(data)
