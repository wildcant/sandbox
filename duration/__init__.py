"""Parse duration strings like "1h30m" into an exact Duration value.

See README.md for the grammar.
"""

from ._core import Duration, DurationParseError
from ._parse import parse_duration

__all__ = ["Duration", "DurationParseError", "parse_duration"]
