"""
pydisc.channels
~~~~~~~~~~~~~~~

Submodule that contains everything channel related.

For an abstraction of the channel design, check :class:`pydisc.abc.Channel`.
"""

from .core import GuildChannel
from .text import TextChannel


__all__ = (
    "GuildChannel",
    "TextChannel",
)
