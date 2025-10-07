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

from typing import Any, Self, TypeVar
from enum import Enum as Enumb

E = TypeVar("E", bound="Enum")

__all__ = (
    "Enum",
    "InteractionType",
    "InteractionContextType",
    "CommandType",
    "EntryPointHandlerType",
    "CommandOptionType",
    "Locale",
    "ChannelType",
    "CommandPermissionType",
    "ComponentType",
    "ButtonStyle",
    "TextStyle",
    "SelectDefaultValueType",
    "ApplicationRoleConnectionMetadataType",
    "SeparatorSpacing",
    "TeamMembershipState",
    "TeamMemberRole",
    "NameplatePalette",
    "IntegrationType",
    "IntegrationExpireBehavior",
    "AutoModEventType",
    "AutoModTriggerType",
    "AutoModKeywordPresetType",
    "AutoModActionType",
    "PermissionOverwriteType",
    "PollLayoutType",
    "MessageType",
    "Status",
    "ActivityType",
    "ActivityStatusDisplayType",
    "CommandPermissionOverwriteType",
    "StickerType",
    "MessageReferenceType",
    "MessageActivityType",
    "DefaultAvatarType",
    "try_enum",
)


class Enum(Enumb):

    # This allows for the enum to not break when an unknown value is
    # passed to it, as Discord is so unpredictable 🤷‍♂️
    @classmethod
    def _missing_(cls, value: object) -> Self:
        name = f"unknown_{value}"
        if name in cls.__members__:
            return cls.__members__[name]

        obj = object.__new__(cls)
        obj._name_ = name
        obj._value_ = value

        cls._member_map_[name] = obj
        cls._value2member_map_[value] = obj
        return obj


"""
TODO: MAYBE, JUST MAYBE, document all enum members

most of them were left undocumented because they were like already
described by the enum name. such as ActivityType.playing, but would
be nice to have them documented.
"""


class InteractionType(Enum):
    """Represents an interaction type."""

    ping = 1
    """A ping interaction."""
    command = 2
    """A command interaction."""
    component = 3
    """A component interaction."""
    autocomplete = 4
    """An autocomplete interaction."""
    modal = 5
    """A modal interaction."""


class InteractionContextType(Enum):
    """Represents the context where an interaction was triggered from."""

    guild = 0
    """Interaction was triggered from a guild."""
    dms = 1
    """Interaction was triggered from the bot's DM."""
    private_channel = 2
    """Interaction was triggered from a private channel."""


class CommandType(Enum):
    """Represents a command type."""

    chat_input = 1
    """Slash commands; a text-based command that shows up when a user types ``/``."""
    user = 2
    """A UI-based command that shows up when you right click or tap on a user."""
    message = 3
    """A UI-based command that shows up when you right click or tap on a message."""
    entry_point = 4
    """A UI-based command that represents the primary way to invoke an app's activity."""


class EntryPointHandlerType(Enum):
    """Represents the type of handler for an entry point command."""

    app_handler = 1
    """The app handles the interaction."""
    launch_activity = 2
    """Discord automatically launches the activity without requiring the bot's intervention."""


class CommandOptionType(Enum):
    """Represents a command's option type."""

    subcommand = 1
    """A subcommand."""
    subcommand_group = 2
    """A subcommand group."""
    string = 3
    """A string option."""
    integer = 4
    """An integer option. Ranged between -2^53 and 2^53. Does not support snowflakes."""
    boolean = 5
    """A boolean option."""
    user = 6
    """A user select option."""
    channel = 7
    """A channel select option. Includes all channel types and categories."""
    role = 8
    """A role select option."""
    mentionable = 9
    """A role and user select option."""
    number = 10
    """A floating point number option. Ranged between - 2^53 and 2^53. Does not support snowflakes."""
    attachment = 11
    """An attachment option."""

    def _join(self, other: CommandOptionType) -> CommandOptionType:
        if other is CommandOptionType.integer:
            if self in (CommandOptionType.number, CommandOptionType.integer):
                return CommandOptionType.number
            else:
                raise ValueError("integer can only be combined with a floating (number) or integer")
        elif (other is CommandOptionType.role and self is CommandOptionType.user) or (
            other is CommandOptionType.user and self is CommandOptionType.role
        ):
            return CommandOptionType.mentionable
        else:
            raise ValueError(f"{self} can not be mixed with {other}")

    @classmethod
    def from_type(cls, typ: Any) -> CommandOptionType:
        from pydisc.role import Role
        from pydisc.attachment import Attachment
        from pydisc.abc import User, Channel

        if issubclass(typ, Role):
            return cls.role
        elif issubclass(typ, User):
            return cls.user
        elif issubclass(typ, Channel):
            return cls.channel
        elif issubclass(typ, Attachment):
            return cls.attachment
        elif typ is int:
            return cls.integer
        elif typ is float:
            return cls.number
        elif typ is bool:
            return cls.boolean
        elif typ is str:
            return cls.string
        else:
            raise TypeError(f"unsupported option type: {typ}")


class Locale(Enum):
    """Represents all locales Discord supports."""

    indonesian = 'id'
    danish = 'da'
    german = 'de'
    british_english = 'en-GB'
    american_english = 'en-US'
    spanish = 'es-ES'
    latin_american_spanish = 'es-419'
    french = 'fr'
    croatian = 'hr'
    italian = 'it'
    lithuanian = 'lt'
    hungarian = 'hu'
    dutch = 'nl'
    norwegian = 'no'
    polish = 'pl'
    brazilian_portuguese = 'pt-BR'
    romanian = 'ro'
    finnish = 'fi'
    swedish = 'sv-SE'
    vietnamese = 'vi'
    turkish = 'tr'
    czech = 'cs'
    greek = 'el'
    bulgarian = 'bg'
    russian = 'ru'
    ukranian = 'uk'
    hindi = 'hi'
    thai = 'th'
    chinese = 'zh-CN'
    japanese = 'ja'
    taiwan_chinese = 'zh-TW'
    korean = 'ko'


class ChannelType(Enum):
    """Represents all channel types."""

    text = 0
    """A text channel within a guild."""
    dm = 1
    """A direct message channel between users."""
    voice = 2
    """A voice channel within a guild."""
    group_dm = 3
    """A direct message channel between multiple users."""
    category = 4
    """An organizational category that contains up to 50 channels."""
    announcement = 5
    """A channel that users can follow and crosspost into their own guild, aka news channels."""
    announcement_thread = 10
    """A temporary sub-channel within an announcement channel."""
    public_thread = 11
    """A temporary sub-channel within a text or forum channel."""
    private_thread = 12
    """A temporary sub-channel within a text channel only viewable by those who are invited or those with :attr:`Permissions.manage_threads` permissions."""
    stage = 13
    """A voice channel for hosting events with an audience."""
    directory = 14
    """The channel in a hub containing the listed guilds."""
    forum = 15
    """A thread-only channel."""
    media = 16
    """A thread-only channel. Similar to forum channels, but different."""


class CommandPermissionType(Enum):
    """Represents a command permission's type."""

    role = 1
    user = 2
    channel = 3


class ComponentType(Enum):
    """Represents a message component type."""

    action_row = 1
    button = 2
    string_select = 3
    select = 3
    text_input = 4
    user_select = 5
    role_select = 6
    mentionable_select = 7
    channel_select = 8
    section = 9
    text_display = 10
    thumbnail = 11
    media_gallery = 12
    file_display = 13
    separator = 14
    container = 17
    label = 18
    file_upload = 19


class ButtonStyle(Enum):
    """Represents button styles."""

    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5
    premium = 6

    blurple = 1
    grey = 2
    gray = 2
    green = 3
    red = 4
    url = 5
    sku = 6


class TextStyle(Enum):
    """Represents a text input's styles."""

    short = 1
    paragraph = 2

    long = 2


class SelectDefaultValueType(Enum):
    """Represents a select default value type."""

    user = "user"
    role = "role"
    channel = "channel"


class ApplicationRoleConnectionMetadataType(Enum):
    """Represents an application role connection metadata type."""

    # i don't really understand the meaning of this lol
    integer_less_or_equal = 1
    integer_greater_or_equal = 2
    integer_equal = 3
    integer_not_equal = 4
    datetime_less_or_equal = 5
    datetime_greater_or_equal = 6
    boolean_equal = 7
    boolean_not_equal = 8


class SeparatorSpacing(Enum):
    """Represents a separator spacing type."""

    small = 1
    large = 2


class TeamMembershipState(Enum):
    """Represents the state of a team member."""

    invited = 1
    accepted = 2


class TeamMemberRole(Enum):
    """Represents a role of a team member."""

    owner = None
    admin = "admin"
    developer = "developer"
    read_only = "read_only"


class NameplatePalette(Enum):
    """The nameplate palette of a :class:`Nameplate`."""

    crimson = "crimson"
    berry = "berry"
    sky = "sky"
    teal = "teal"
    forest = "forest"
    bubble_gum = "bubble_gum"
    violet = "violet"
    cobalt = "cobalt"
    clover = "clover"
    lemon = "lemon"
    white = "white"


class IntegrationType(Enum):
    """Represents an integration type."""

    twitch = "twitch"
    youtube = "youtube"
    discord = "discord"
    guild_subscription = "guild_subscription"


class IntegrationExpireBehavior(Enum):
    """Represents an integration's expire behavior."""

    remove_role = 0
    kick = 1


class AutoModEventType(Enum):
    """Represents the event that must happen for an auto mod rule to be executed."""

    message_send = 1
    """The auto mod will be triggered on each message sent."""
    member_update = 2
    """The auto mod will be triggered when a member updates its profile."""


class AutoModTriggerType(Enum):
    """Represents the type of content that can trigger an auto mod rule."""

    keyword = 1
    """The auto mod can be triggered if the content of a message matches a keyword."""
    spam = 3
    """The auto mod can be triggered if the content of a message is generic spam."""
    keyword_preset = 4
    """The auto mod can be triggered if the content of a message matches a Discord-internal keyword list."""
    mention_spam = 5
    """The auto mod can be triggered if the content of a message contains more unique mentions than allowed."""
    member_profile = 6
    """The auto mod can be triggered if a member profile contains any word from a user-defined keyword list."""


class AutoModKeywordPresetType(Enum):
    """Represents the keyword preset type for an auto mod rule metadata."""

    profanity = 1
    """Checks if messages contain words considered as profanity."""
    sexual_content = 2
    """Checks if messages contain words that refer to sexually explicit behavior or activity."""
    slurs = 3
    """Checks if messages contain personal insults or words that may be considered as hate speech."""


class AutoModActionType(Enum):
    """Represents the action type done when an auto mod rule is triggered."""

    block_message = 1
    send_alert_message = 2
    timeout = 3
    block_member_interaction = 4


class PermissionOverwriteType(Enum):
    """Represents a permission overwrite type."""

    role = 0
    member = 1


class PollLayoutType(Enum):
    """Represents how a poll answer's are displayed."""

    default = 0


class MessageType(Enum):
    """Represents the type of a message."""

    default = 0
    recipient_add = 1
    recipient_remove = 2
    call = 3
    channel_name_change = 4
    channel_icon_change = 5
    pins_add = 6
    new_member = 7
    premium_guild_subscription = 8
    premium_guild_tier_1 = 9
    premium_guild_tier_2 = 10
    premium_guild_tier_3 = 11
    channel_follow_add = 12
    guild_stream = 13
    guild_discovery_disqualified = 14
    guild_discovery_requalified = 15
    guild_discovery_grace_period_initial_warning = 16
    guild_discovery_grace_period_final_warning = 17
    thread_created = 18
    reply = 19
    chat_input_command = 20
    thread_starter_message = 21
    guild_invite_reminder = 22
    context_menu_command = 23
    auto_moderation_action = 24
    role_subscription_purchase = 25
    interaction_premium_upsell = 26
    stage_start = 27
    stage_end = 28
    stage_speaker = 29
    stage_raise_hand = 30
    stage_topic = 31
    guild_application_premium_subscription = 32
    guild_incident_alert_mode_enabled = 36
    guild_incident_alert_mode_disabled = 37
    guild_incident_report_raid = 38
    guild_incident_report_false_alarm = 39
    purchase_notification = 44
    poll_result = 46
    emoji_added = 63


class Status(Enum):
    """Represents a user's status."""

    online = "online"
    idle = "idle"
    dnd = "dnd"
    invisible = "invisible"
    offline = "offline"


class ActivityType(Enum):
    """Represents an activity type."""

    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5


class ActivityStatusDisplayType(Enum):
    """Represents the way an activity is displayed in a user's profile."""

    activity_name = 0
    """Displays the activity name: "Listening to Spotify" """
    state = 1
    """Displays the activity state: "Listening to Rick Astley" """
    details = 2
    """Displays the activity details: "Listening to Never Gonna Give You Up" """


class CommandPermissionOverwriteType(Enum):
    """Represents an application command permission overwrite type."""

    role = 1
    user = 2
    channel = 3


class StickerType(Enum):
    """Represents a sticker type."""

    standard = 1
    guild = 2


class StickerFormatType(Enum):
    """Represents a sticker's image format type."""

    png = 1
    apng = 2
    lottie = 3
    gif = 4


class MessageReferenceType(Enum):
    """Represents the type of message reference to use when creating a message."""

    default = 0
    forward = 1


class MessageActivityType(Enum):
    """The activity type of a message."""

    join = 1
    spectate = 2
    listen = 3
    join_request = 4


class DefaultAvatarType(Enum):
    """Represents the default avatar type for a user."""

    blurple = 0
    gray = 1
    green = 2
    orange = 3
    red = 4
    pink = 5


def try_enum(cls: type[E], value: Any) -> E:
    return cls(value)
