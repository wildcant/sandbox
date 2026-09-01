"""Parse duration strings like "1h30m" into an exact Duration value, and back.

See README.md for the grammar.
"""

from ._core import Duration, DurationParseError
from ._format import format_duration
from ._parse import parse_duration

__all__ = ["Duration", "DurationParseError", "format_duration", "parse_duration"]
