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

import datetime
from typing import TYPE_CHECKING, Any, Self

from .enums import PollLayoutType, MessageType, try_enum
from .emoji import Emoji
from .missing import MissingOr, MISSING
from .utils import parse_time

if TYPE_CHECKING:
    from .cache._types import CacheProtocol
    from .message import Message

__all__ = (
    "PollMedia",
    "PollAnswer",
    "Poll",
)


class PollMedia:
    """Represents the media passed to a poll item."""

    def __init__(self, *, text: str, emoji: Emoji | str | None = None) -> None:
        self.text: str = text
        self.emoji: Emoji | None = Emoji.from_str(emoji) if isinstance(emoji, str) else emoji

    def to_dict(self) -> dict[str, Any]:
        pd: dict[str, Any] = {"text": self.text}
        if self.emoji is not None:
            pd["emoji"] = self.emoji.to_dict()
        return pd

    @classmethod
    def from_dict(cls, data: dict[str, Any], state: CacheProtocol) -> PollMedia:
        self = cls(text=data["text"])
        if emoji := data.get("emoji"):
            self.emoji = Emoji.from_dict(emoji, state)
        return self


class PollAnswer:
    """Represents a poll answer."""

    def __init__(
        self,
        *,
        media: PollMedia,
        id: MissingOr[int] = MISSING,
    ) -> None:
        self.media: PollMedia = media
        self._id: MissingOr[int] = id
        self._poll: MissingOr[Poll] = MISSING
        self._vote_count: int = 0
        self._self_voted: bool = False
        self._victor: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any], cache: CacheProtocol, poll: Poll) -> PollAnswer:
        self = PollAnswer(
            media=PollMedia.from_dict(data["media"], cache),
            id=int(data["answer_id"]),
        )
        self._poll = poll
        return self

    def to_dict(self) -> dict[str, Any]:
        return {"poll_media": self.media.to_dict()}

    def _handle_vote(self, added: bool, self_voted: bool) -> None:
        if added:
            self._vote_count += 1
        else:
            self._vote_count = max(self._vote_count - 1, 0)
        self._self_voted = self_voted

    def _update_with_results(self, data: dict[str, Any]) -> None:
        self._vote_count = int(data["count"])
        self._self_voted = data["me_voted"]

    @property
    def id(self) -> int:
        """Returns the ID of this poll answer."""
        if self._id is MISSING:
            raise RuntimeError("no id is set for this answer.")
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    @property
    def text(self) -> str:
        """A shortcut for :attr:`media.text <PollMedia.text>`."""
        return self.media.text

    @text.setter
    def text(self, value: str) -> None:
        self.media.text = value

    @property
    def emoji(self) -> Emoji | None:
        """A shortcut for :attr:`media.emoji <PollMedia.emoji>`."""
        return self.media.emoji

    @emoji.setter
    def emoji(self, value: Emoji | str | None) -> None:
        if value is None:
            self.media.emoji = None
        elif isinstance(value, str):
            self.media.emoji = Emoji.from_str(value)
        elif isinstance(value, Emoji):
            self.media.emoji = value
        else:
            raise TypeError(f"expected Emoji, str or None, got {value.__class__.__name__} instead.")

    @property
    def poll(self) -> Poll:
        """Returns the parent poll of this answer."""
        if self._poll is MISSING:
            raise RuntimeError("no poll is set for this answer.")
        return self._poll

    @property
    def vote_count(self) -> int:
        """Returns an approximate vote count of this poll answer.

        If the poll has finished, then this count is exact.
        """
        return self._vote_count

    @property
    def self_voted(self) -> bool:
        """Whether the current user has voted to this answer.

        If the poll has finished, then this is an exact result.
        """
        return self._self_voted

    @property
    def victor(self) -> bool:
        """Whether this answer was the one with the most votes
        when the poll finished.

        This will always return ``False`` for polls that have not
        yet finished.
        """
        return self._victor

    def copy(self) -> PollAnswer:
        """Returns a stateless copy of this answer."""
        return PollAnswer(
            media=self.media,
            id=self.id,
        )


class Poll:
    """Represents a message's poll."""

    def __init__(
        self,
        question: PollMedia,
        duration: datetime.timedelta,
        *,
        multiple_answers: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        self.question: PollMedia = question
        self._answers: dict[int, PollAnswer] = {}
        self.duration: datetime.timedelta = duration

        self.multiple_answers: bool = multiple_answers
        self.layout_type: PollLayoutType = layout_type

        self._message: Message | None = None
        self._finalized: bool = False
        self._expiry: datetime.datetime | None = None
        self._total_votes: int | None = None
        self._victor_answer_id: int | None = None

    def _update_from_message(self, message: Message) -> None:
        if not message.poll:
            return

        self._message = message
        poll = message.poll
        self._expiry = poll.expires_at
        self._finalized = poll._finalized
        self._answers = poll._answers

        if poll._finalized:
            self._update_results_from_message(message)

    def _update_results_from_message(self, message: Message) -> None:
        if message.type is not MessageType.poll_result or not message.embeds:
            return

        result = message.embeds[0]
        fields: dict[str, str] = {f.name: f.value for f in result.fields}

        total_votes = fields.get("total_votes")
        if total_votes is not None:
            self._total_votes = int(total_votes)

        victor_answer = fields.get("victor_answer_id")
        if victor_answer is None:
            return

        self._victor_answer_id = int(victor_answer)
        victor_answer_votes = fields["victor_answer_votes"]

        answer = self._answers[self._victor_answer_id]
        answer._victor = True
        answer._vote_count = int(victor_answer_votes)
        self._answers[answer.id] = answer 

    def _update_results(self, data: dict[str, Any]) -> None:
        self._finalized = data["is_finalized"]

        for count in data["answer_counts"]:
            answer = self.get_answer(int(count["id"]))
            if not answer:
                continue
            answer._update_with_results(count)

    def _handle_vote(self, answer_id: int, added: bool, self_voted: bool) -> None:
        answer = self.get_answer(answer_id)
        if not answer:
            return
        answer._handle_vote(added, self_voted)

    def get_answer(self, id: int, /) -> PollAnswer | None:
        """Gets an answer with :attr:`PollAnswer.id` as ``id``, or ``None``."""
        return self._answers.get(id)

    @classmethod
    def from_dict(cls, data: dict[str, Any], message: Message) -> Poll:
        multiselect = data.get("allow_multiselect", False)
        layout = try_enum(PollLayoutType, data.get("layout_type", 1))
        question = PollMedia.from_dict(data["question"], message._cache)
        expiry = parse_time(data["expiry"])
        # duration = expiry - message.created_at
        # as this may be a few nanos away from the actual duration, we should round it
        duration = datetime.timedelta(hours=round((expiry - message.created_at).total_seconds() / 3600))

        self = Poll(
            duration=duration,
            question=question,
            layout_type=layout,
            multiple_answers=multiselect,
        )
        self._answers = {
            int(answer["answer_id"]): PollAnswer.from_dict(answer, message._cache, self)
            for answer in data["answers"]
        }
        self._message = message
        self._expiry = expiry

        try:
            self._update_results(data["results"])
        except KeyError:
            pass

        return self

    @property
    def answers(self) -> list[PollAnswer]:
        """Returns the poll's answers."""
        return list(self._answers.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_multiselect": self.multiple_answers,
            "question": self.question.to_dict(),
            "duration": self.duration.total_seconds() / 3600,
            "layout_type": self.layout_type.value,
            "answers": [a.to_dict() for a in self.answers]
        }

    @property
    def victor_answer_id(self) -> int | None:
        """Returns the victor answer ID of this poll.

        If it has not finished, then this will return ``None``.
        """
        return self._victor_answer_id

    @property
    def victor_answer(self) -> PollAnswer | None:
        """Returns the victor answer of this poll.

        If it has not finished, or it is not found in this poll, then this will
        return ``None``.
        """
        if self.victor_answer_id is None:
            return None
        return self.get_answer(self.victor_answer_id)

    @property
    def expires_at(self) -> datetime.datetime | None:
        """When this poll expires at.

        This will always be ``None`` for stateless polls.
        """
        return self._expiry

    @property
    def created_at(self) -> datetime.datetime | None:
        """When this poll was created at.

        This will always be ``None`` for stateless polls.
        """
        if self._message is None:
            return None
        return self._message.created_at

    @property
    def message(self) -> Message | None:
        """The message this poll was sent along.

        This will always be ``None`` for not yet sent polls or stateless
        polls.
        """
        return self._message

    @property
    def total_votes(self) -> int:
        """Returns an approximate amount of the total votes in this poll.

        If this poll is stateful, the count will be exact.
        """
        if self._total_votes is not None:
            return self._total_votes
        return sum([a.vote_count for a in self.answers])

    def is_finalized(self) -> bool:
        """Whether this poll haz finalized.

        This will always return ``False`` for stateless polls.
        """
        return self._finalized

    def copy(self) -> Poll:
        """Returns a stateless copy of this poll."""

        new = Poll(
            self.question,
            self.duration,
            multiple_answers=self.multiple_answers,
            layout_type=self.layout_type,
        )

        # answers may have an state attached to it so
        # we recreate them.
        for answer in self.answers:
            new.append_answer(answer.copy())

        return new

    def add_answer(
        self,
        *,
        media: PollMedia,
    ) -> Self:
        """Adds an answer to this poll.

        If you want to add an already constructed :class:`PollAnswer` object,
        consider using :meth:`append_answer`.
        """
        ans = PollAnswer(
            media=media,
            id=len(self.answers) + 1,
        )
        self.append_answer(ans)
        return self

    def append_answer(self, answer: PollAnswer, /) -> Self:
        """Appends an already constructed :class:`PollAnswer` object to this poll."""
        if answer.id is MISSING:
            answer.id = len(self.answers) + 1
        self._answers[answer.id] = answer
        return self
