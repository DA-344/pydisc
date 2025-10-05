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

from enum import Flag

from .utils import class_property

__all__ = (
    "PublicUserFlags",
    "ChannelFlags",
    "SystemChannelFlags",
    "MessageFlags",
    "Intents",
    "AttachmentFlags",
    "Permissions",
    "EmbedFlags",
    "ActivityFlags",
)


class PublicUserFlags(Flag):
    """Represent the public flags of a :class:`User`."""

    staff = 1 << 0
    """Whether the user is a staff."""
    partner = 1 << 1
    """Whether the user is the owner of a partenered server."""
    hypesquad = 1 << 2
    """Whether the user is part of the hypesquad events."""
    bug_hunter_level_1 = 1 << 3
    """Whether the user is level 1 bug hunter."""
    hypesquad_bravery = 1 << 6
    """Whether the user hypesquad house is Bravery."""
    hypesquad_brilliance = 1 << 7
    """Whether the user hypesquad house is Brilliance."""
    hypesquad_balance = 1 << 8
    """Whether the user hypesquad house is Balance."""
    early_supporter = 1 << 9
    """Whether the user is an early supported."""
    team_pseudo_user = 1 << 10
    """Whether this user is really a team."""
    bug_hunter_level_2 = 1 << 14
    """Whether the user is level 2 bug hunter."""
    verified_bot = 1 << 16
    """Whether the user is a verified bot user."""
    verified_developer = 1 << 17
    """Whether the user is a verified bot developer."""
    certified_moderator = 1 << 18
    """Whether the user is a Discord certified moderator."""
    bot_http_interactions = 1 << 19
    """Whether the user is a HTTP-only bot."""
    active_developer = 1 << 22
    """Whether the user is an active developer."""


class ChannelFlags(Flag):
    """Represent a channel's flags."""

    pinned = 1 << 1
    """In case of a thread in a forum, whether it is pinned."""
    requires_tag = 1 << 4
    """In case of a forum, whether at least 1 tag is required when creating a thread."""
    hide_media_download_options = 1 << 15
    """In case of a media forum, whether the download options are hidden from messages."""


class SystemChannelFlags(Flag):
    """Represent the flags of a guild's system channel."""

    suppress_join_notifications = 1 << 0
    """Whether join notifications are suppressed."""
    suppress_premium_subscriptions = 1 << 1
    """Whether premium subscriptions (aka Nitro Boosting) messages are suppressed."""
    suppress_guild_reminder_notifications = 1 << 2
    """Whether "helpful tips" messages are suppressed."""
    suppress_join_notification_replies = 1 << 3
    """Whether the "Reply with a sticker" button is hidden from join messages."""
    suppress_role_subs_notifications = 1 << 4
    """Whether role subscriptions buy and renewal messages are suppressed."""
    suppress_role_subs_notification_replies = 1 << 5
    """Whether the "Reply with a sticker" button is hidden from role subscription messages."""
    suppress_emoji_added = 1 << 8
    """Whether a message is sent when an emoji is added."""


class MessageFlags(Flag):
    """Represent the flags of a message."""

    crossposted = 1 << 0
    """Whether this message has been crossposted (aka published) to its follower channels."""
    is_crossposted = 1 << 1
    """Whether this message is crossposted from another server."""
    suppress_embeds = 1 << 2
    """Whether embeds are suppressed from this embed."""
    source_message_deleted = 1 << 3
    """Whether the source message of the crosspost has been deleted."""
    urgent = 1 << 4
    """Whether this message is from an urgent system."""
    has_thread = 1 << 5
    """Whether this message has a thread attached to it."""
    ephemeral = 1 << 6
    """Whether this message is ephemeral."""
    loading = 1 << 7
    """Whether this message is in a "Bot is thinking..." state."""
    failed_to_mention_some_roles_in_thread = 1 << 8
    """Whether this message failed to add some roles to the respective thread."""
    suppress_notifications = 1 << 12
    """Whether this message triggers push and desktop notifications."""
    voice_message = 1 << 13
    """Whether this message is a voice message."""
    has_snapshot = 1 << 14
    """Whether this message has any forwarded content."""
    components_v2 = 1 << 15
    """Whether this message has components v2."""


class Intents(Flag):
    """Represents the intents for a gateway connection."""

    guilds = 1 << 0
    """Whether the following guild-related events are available:

    - ``guild_create``
    - ``guild_update``
    - ``guild_delete``
    - ``guild_role_create``
    - ``guild_role_update``
    - ``guild_role_delete``
    - ``channel_create``
    - ``channel_update``
    - ``channel_delete``
    - ``channel_pins_update``
    - ``thread_create``
    - ``thread_update``
    - ``thread_delete``
    - ``thread_list_sync``
    - ``thread_member_update``
    - ``thread_members_update``
    - ``stage_instance_create``
    - ``stage_instance_update``
    - ``stage_instance_delete``
    """
    guild_members = 1 << 1
    """Whether the folloing guild member-related events are available:

    .. warning::

        This is a priviliged intent that must explicitly be opted-in in
        the Developer Portal in order to be used here.

    - ``guild_member_add``
    - ``guild_member_update``
    - ``guild_member_remove``
    - ``thread_members_update``
    """
    guild_moderation = 1 << 2
    """Whether the folloing guild moderation-related events are available:

    - ``guild_audit_log_entry_create``
    - ``guild_ban_add``
    - ``guild_ban_remove``
    """
    guild_expressions = 1 << 3
    """Whether the following guild expression-related events are available:

    - ``guild_emojis_update``
    - ``guild_stickers_update``
    - ``guild_soundboard_sound_create``
    - ``guild_soundboard_sound_update``
    - ``guild_soundboard_sound_delete``
    - ``guild_soundboard_sounds_update``
    """
    guild_integrations = 1 << 4
    """Whether the following guild integration-related events are available:

    - ``guild_integrations_update``
    - ``integration_create``
    - ``integration_update``
    - ``integration_delete``
    """
    guild_webhooks = 1 << 5
    """Whether the following guild webhook-related events are available:

    - ``webhooks_update``
    """
    guild_invites = 1 << 6
    """Whether the following guild invite-related events are available:

    - ``invite_create``
    - ``invite_delete``
    """
    guild_voice_states = 1 << 7
    """Whether the following guild voice state-related events are available:

    - ``voice_channel_effect_send``
    - ``voice_state_update``
    """
    guild_presences = 1 << 8
    """Whether the following guild presence-related events are available:

    .. warning::

        This is a priviliged intent that must explicitly be opted-in in
        the Developer Portal in order to be used here.

    - ``presence_update``
    """
    guild_messages = 1 << 9
    """Whether the following guild message-related events are available:

    - ``message_create``
    - ``message_update``
    - ``message_delete``
    - ``message_bulk_delete``
    """
    guild_message_reactions = 1 << 10
    """Whether the following guild message reaction-related events are available:

    - ``message_reaction_add``
    - ``message_reaction_remove``
    - ``message_reaction_remove_all``
    - ``message_reaction_emoji_remove``
    """
    guild_message_typing = 1 << 11
    """Whether the following guild message typing-related events are available:

    - ``typing_start``
    """
    direct_messages = 1 << 12
    """Whether the following direct message-related events are available:

    - ``message_create``
    - ``message_update``
    - ``message_delete``
    - ``channel_pins_update``
    """
    direct_message_reactions = 1 << 13
    """Whether the following direct message reaction-related events are available:

    - ``message_reaction_add``
    - ``message_reaction_remove``
    - ``message_reaction_remove_all``
    - ``message_reaction_emoji_remove``
    """
    direct_message_typing = 1 << 14
    """Whether the following direct message typing-related events are available:

    - ``typing_start``
    """
    message_content = 1 << 15
    """Whether you can access the following attributes in messages:

    .. warning::

        This is a priviliged intent that must explicitly be opted-in in
        the Developer Portal in order to be used here.

    - :attr:`Message.content`
    - :attr:`Message.embeds`
    - :attr:`Message.attachments`
    - :attr:`Message.components`
    - :attr:`Message.poll`

    In the case the bot is:

    - not mentioned in the message body
    - the message is not sent in the bot DMs
    - the message was not sent by the bot
    """
    guild_scheduled_events = 1 << 16
    """Whether the following guild scheduled-event-related events are available:

    - ``guild_scheduled_event_create``
    - ``guild_scheduled_event_update``
    - ``guild_scheduled_event_delete``
    - ``guild_scheduled_event_user_add``
    - ``guild_scheduled_event_user_remove``
    """
    auto_moderation_configuration = 1 << 20
    """Whether the following guild automod configuration-related events are available:

    - ``automod_rule_create``
    - ``automod_rule_update``
    - ``automod_rule_delete``
    """
    auto_moderation_execution = 1 << 21
    """Whether the following guild automod execution-related events are available:

    - ``automod_action_execution``
    """
    guild_message_polls = 1 << 24
    """Whether the following guild messages poll-related events are available:

    - ``message_poll_vote_add``
    - ``message_poll_vote_remove``
    """
    direct_message_polls = 1 << 25
    """Whether the following direct messages poll-related events are available:

    - ``message_poll_vote_add``
    - ``message_poll_vote_remove``
    """

    @class_property
    def messages(cls) -> Intents:
        """A shortcut for ``Intents.guild_messages | Intents.direct_messages``"""
        return cls.guild_messages | cls.direct_messages

    @class_property
    def message_typing(cls) -> Intents:
        """An alias for ``Intents.guild_message_typing | Intents.direct_message_typing``"""
        return cls.guild_message_typing | cls.direct_message_typing

    @class_property
    def auto_moderation(cls) -> Intents:
        """An alias for ``Intents.auto_moderation_configuration | Intents.auto_moderation_execution``"""
        return cls.auto_moderation_configuration | cls.auto_moderation_execution

    @class_property
    def message_polls(cls) -> Intents:
        """An alias for ``Intents.guild_message_polls | Intents.direct_message_polls``"""
        return cls.guild_message_polls | cls.direct_message_polls

    @class_property
    def message_reactions(cls) -> Intents:
        """An alias for ``Intents.guild_message_reactions | Intents.direct_message_reactions``"""
        return cls.guild_message_reactions | cls.direct_message_reactions

    @classmethod
    def all(cls) -> Intents:
        """Returns an ``Intents`` instace with all flags set."""
        return (
            cls.guilds
            | cls.guild_members
            | cls.guild_moderation
            | cls.guild_expressions
            | cls.guild_integrations
            | cls.guild_webhooks
            | cls.guild_invites
            | cls.guild_voice_states
            | cls.guild_presences
            | cls.messages
            | cls.message_reactions
            | cls.message_typing
            | cls.message_content
            | cls.guild_scheduled_events
            | cls.auto_moderation
            | cls.message_polls
        )

    @classmethod
    def default(cls) -> Intents:
        """Returns a ``Intents`` instance with all flags set, except for priviliged."""
        self = cls.all()
        self &= ~cls.message_content
        self &= ~cls.guild_presences
        self &= ~cls.guild_members
        return self


class AttachmentFlags(Flag):
    """Represents an attachment flags."""

    clip = 1 << 0
    """Whether the attachment is a clip."""
    thumbnail = 1 << 1
    """Whether the attachment is a thumbnail."""
    remix = 1 << 2
    """Whether the attachment was created with the "Remix" feature."""
    spoiler = 1 << 3
    """Whether the attachment is flagged as a spoiler."""
    contains_explicit_media = 1 << 4
    """Whether the attachment contains explicit media."""
    animated = 1 << 5
    """Whether the attachment is an animated image."""


class Permissions(Flag):
    """Represents the permissions of a Discord object."""

    def __new__(cls, value: int = 0, **perms: bool) -> None:
        if not isinstance(value, int):
            raise TypeError(f"expected an int, got a {value.__class__.__name__}")

        self = super().__new__(cls, value)

        for perm, toggle in perms.items():
            try:
                f = getattr(cls, perm)
            except AttributeError:
                raise AttributeError(f"{perm} is not a valid permission")

            if toggle is True:
                self |= f
            elif toggle is False:
                self &= ~f
            else:
                raise TypeError(f"expected True or False for permission {perm}, got {toggle} instead")

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.value & other.value) == self.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.value | other.value) == self.value

    __le__ = __lt__
    __ge__ = __gt__

    @classmethod
    def none(cls) -> Permissions:
        """Returns a Permissions object with no flag set."""
        return Permissions(0)

    @classmethod
    def all(cls) -> Permissions:
        """Returns a Permissions object with all flags set."""
        return (
            Permissions.general()
            | Permissions.membership()
            | Permissions.text_channels()
            | Permissions.voice_channels()
            | Permissions.apps()
            | Permissions.stage_channels()
            | Permissions.events()
            | Permissions.advanced()
        )

    @classmethod
    def general(cls) -> Permissions:
        """Returns a Permissions object with all the UI "General" section permissions enabled."""
        return (
            Permissions.view_channels
            | Permissions.manage_channels
            | Permissions.manage_roles
            | Permissions.create_guild_expressions
            | Permissions.manage_guild_expressions
            | Permissions.view_audit_log
            | Permissions.view_guild_insights
            | Permissions.manage_webhooks
            | Permissions.manage_guild
        )

    @classmethod
    def membership(cls) -> Permissions:
        """Returns a Permissions obejct with all the UI "Membership" section permissions enabled."""
        return (
            Permissions.create_instant_invite
            | Permissions.change_nickname
            | Permissions.manage_nicknames
            | Permissions.ban_members
            | Permissions.moderate_members
        )

    @classmethod
    def text_channels(cls) -> Permissions:
        """Returns a Permissions object with all the UI "Text channels" section permissions enabled."""
        return (
            Permissions.send_messages
            | Permissions.send_messages_in_threads
            | Permissions.create_public_threads
            | Permissions.create_private_threads
            | Permissions.embed_links
            | Permissions.attach_files
            | Permissions.add_reactions
            | Permissions.use_external_emojis
            | Permissions.use_external_stickers
            | Permissions.mention_everyone
            | Permissions.manage_messages
            | Permissions.pin_messages
            | Permissions.manage_threads
            | Permissions.read_message_history
            | Permissions.send_tts_messages
            | Permissions.send_voice_messages
            | Permissions.send_polls
        )

    @classmethod
    def voice_channels(cls) -> Permissions:
        """Returns a Permissions object with all the UI "Voice channels" section permissions enabled."""
        return (
            Permissions.connect
            | Permissions.speak
            | Permissions.stream
            | Permissions.use_soundboard
            | Permissions.use_external_sounds
            | Permissions.use_vad
            | Permissions.priority_speaker
            | Permissions.mute_members
            | Permissions.deafen_members
            | Permissions.move_members
        )

    @classmethod
    def apps(cls) -> Permissions:
        """Returns a Permissions object with all the UI "Apps" section permissions enabled."""
        return Permissions.use_application_commands | Permissions.use_embedded_activities | Permissions.use_external_apps

    @classmethod
    def stage_channels(cls) -> Permissions:
        """Returns a Permissions obejct with all the UI "Stage channels" section permissions enabled."""
        return Permissions.request_to_speak

    @classmethod
    def events(cls) -> Permissions:
        """Returns a Permissions object with all the UI "Events" section permissions enabled."""
        return Permissions.create_events | Permissions.manage_events

    @classmethod
    def advanced(cls) -> Permissions:
        """Returns a Permissions object with all the UI "Advanced" section permissions enabled."""
        return Permissions.administrator

    create_instant_invite = 1 << 0
    """Allows creating instant invites."""
    kick_members = 1 << 1
    """Allows kicking members."""
    ban_members = 1 << 2
    """Allows banning members."""
    administrator = 1 << 3
    """Allows all permissions and bypasses channel permission overwrites."""
    manage_channels = 1 << 4
    """Allows management and editing of channels."""
    manage_guild = 1 << 5
    """Allows management and editing of the guild."""
    add_reactions = 1 << 6
    """Allows adding new reactions to messages."""
    view_audit_log = 1 << 7
    """Allows for viewing the audit log."""
    priority_speaker = 1 << 8
    """Allows using the Priority Speaker in voice channels."""
    stream = 1 << 9
    """Allows the user to go live."""
    view_channels = 1 << 10
    """Allows to view channels."""
    send_messages = 1 << 11
    """Allows sending messages in a channel and creating threads in forum-like."""
    send_tts_messages = 1 << 12
    """Allows for sending /tts messages."""
    manage_messages = 1 << 13
    """Allows for deletion of other users' messages."""
    embed_links = 1 << 14
    """Allows for automatically embedding user links."""
    attach_files = 1 << 15
    """Allows uploading images and files."""
    read_message_history = 1 << 16
    """Allows reading a channel's message history."""
    mention_everyone = 1 << 17
    """Allows using the ``@everyone`` and ``@here`` tags."""
    use_external_emojis = 1 << 18
    """Allows using custom emojis from other guilds."""
    view_guild_insights = 1 << 19
    """Allows viewing a guild's insights."""
    connect = 1 << 20
    """Allows connecting to voice channels."""
    speak = 1 << 21
    """Allows speaking in voice channels."""
    mute_members = 1 << 22
    """Allows muting other members in voice channels."""
    deafen_members = 1 << 23
    """Allows deafening other members in voice channels."""
    move_members = 1 << 24
    """Allows moving members from voice channels."""
    use_vad = 1 << 25
    """Allows using the voice-activity-detection feature in voice channels."""
    change_nickname = 1 << 26
    """Allows changing the self-user nickname in a guild."""
    manage_nicknames = 1 << 27
    """Allows management other member's nicknames."""
    manage_roles = 1 << 28
    """Allows management and editing of roles."""
    manage_webhooks = 1 << 29
    """Allows management and editing of webhooks."""
    manage_guild_expressions = 1 << 30
    """Allows management and editing of guild emojis, stickers, and souboard sounds."""
    use_application_commands = 1 << 31
    """Allows usage of application commands."""
    request_to_speak = 1 << 32
    """Allows sending a Speak Request in stage channels."""
    manage_events = 1 << 33
    """Allows management and editing of scheduled events."""
    manage_threads = 1 << 34
    """Allows management, editing, and archiving of threads. Also allows for seeing private threads."""
    create_public_threads = 1 << 35
    """Allows creating public threads."""
    create_private_threads = 1 << 36
    """Allows creating private threads."""
    use_external_stickers = 1 << 37
    """Allows using custom stickers from other guilds."""
    send_messages_in_threads = 1 << 38
    """Allows sending messages in threads."""
    use_embedded_activities = 1 << 39
    """Allows using Activities"""
    moderate_members = 1 << 40
    """Allows timing-out users."""
    view_creator_monetization_analytics = 1 << 41
    """Allows viewing role subscription insights."""
    use_soundboard = 1 << 42
    """Allows using soundboard sounds in voice channels."""
    create_guild_expressions = 1 << 43
    """Allows creating guild emojis, stickers, and soundboard sounds."""
    create_events = 1 << 44
    """Allows creating schedulede events."""
    use_external_sounds = 1 << 45
    """Allows using soundboard sounds from other guilds."""
    send_voice_messages = 1 << 46
    """Allows sending voice messages."""
    send_polls = 1 << 47
    """Allows creating polls."""
    use_external_apps = 1 << 48
    """Allows using apps installed in a user account that are not added into the guild."""
    pin_messages = 1 << 51
    """Allows pinning and unpinning messages."""


class EmbedFlags(Flag):
    """Represents an embed flags."""

    contains_explicit_media = 1 << 4
    """Whether the embed is flagged as sensitive content."""
    content_inventory_entry = 1 << 5
    """Whether the embed is a reply to an activity card, and is no
    longer displayed.
    """


# thanks discord for the lack of documentation here
class ActivityFlags(Flag):
    """Represents the flags of an activity."""

    instance = 1 << 0
    join = 1 << 1
    spectate = 1 << 2
    join_request = 1 << 3
    sync = 1 << 4
    play = 1 << 5
    party_privacy_friends = 1 << 6
    party_privacy_voice_channel = 1 << 7
    embedded = 1 << 8
