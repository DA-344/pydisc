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

from pydisc.enums import AutoModTriggerType, try_enum
from pydisc.utils import _get_snowflake

from .core import _RichGetterModel, EventModel

__all__ = (
    "AutoModRuleCreate",
    "AutoModRuleUpdate",
    "AutoModRuleDelete",
    "AutoModActionExecution",
)


if TYPE_CHECKING:
    from pydisc.auto_moderation import AutoModRule
    from pydisc.cache._types import CacheProtocol

    class _AutoModEventProxy(_RichGetterModel, AutoModRule):
        data: AutoModRule

else:

    class _AutoModEventProxy(_RichGetterModel):
        def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
            from pydisc.auto_moderation import AutoModRule

            self.data = AutoModRule(data, cache)


AutoModRuleCreate = _AutoModEventProxy
"""Represents an ``on_auto_mod_rule_create`` event payload."""
AutoModRuleUpdate = _AutoModEventProxy
"""Represents an ``on_auto_mod_rule_update`` event payload."""
AutoModRuleDelete = _AutoModEventProxy
"""Represents an ``on_auto_mod_rule_delete`` event payload."""


class AutoModActionExecution(EventModel):
    """Represents an ``on_auto_mod_action_execution`` event payload."""

    def __init__(self, data: dict[str, Any], cache: CacheProtocol) -> None:
        self.guild_id: int = int(data["guild_id"])
        """The guild ID in which the action was executed."""

        from pydisc.auto_moderation import AutoModAction

        self.action: AutoModAction = AutoModAction.from_dict(data["action"])
        """The action that was executed."""

        self.rule_id: int = int(data["rule_id"])
        """The rule ID the action belongs to."""
        self.rule_trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data["rule_trigger_type"])
        """The trigger type of the rule."""
        self.user_id: int = int(data["user_id"])
        """The user ID that actioned the auto mod rule."""
        self.channel_id: int | None = _get_snowflake("channel_id", data)
        """The channel ID in which the content that triggered the action was sent to."""
        self.message_id: int | None = _get_snowflake("message_id", data)
        """The message ID which had the content blocked. This may be ``None`` if the message was blocked
        by Auto Mod or the content that actioned the rule was not a message.
        """
        self.alert_system_message_id: int | None = _get_snowflake("alert_system_message_id", data)
        """The ID of the system message generated as a result of this auto mod rule execution."""
        self.content: str = data["content"]
        """The content that actioned the rule."""
        self.matched_keyword: str | None = data.get("matched_keyword")
        """The words or phrases of the auto mod rule that were matched and triggered it."""
        self.matched_content: str | None = data.get("matched_content")
        """The substring of the auto mod rule that was matched and triggered it."""
