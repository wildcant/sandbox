"""The Duration value type, the parse error, and the unit table both halves share."""

from dataclasses import dataclass

# Units largest first. Parsing walks this order to check that a compound
# duration names its units largest-first, and formatting emits in it.
UNITS = (
    ("d", 86_400_000),
    ("h", 3_600_000),
    ("m", 60_000),
    ("s", 1_000),
    ("ms", 1),
)

# Largest magnitude a parsed duration may carry: the biggest integer an
# IEEE-754 double represents exactly, so a Duration survives a trip through
# JSON or any float-backed store without silently changing value.
MAX_MILLISECONDS = 2**53 - 1


@dataclass(frozen=True)
class Duration:
    """An exact span of time in whole milliseconds, negative for a span backwards.

    Frozen, so it compares by value and hashes.
    """

    milliseconds: int


class DurationParseError(ValueError):
    """Raised when a string is not a valid duration.

    Subclasses ValueError so callers with an existing bad-input handler keep
    catching it, but the type raised is always DurationParseError.
    """

    def __init__(self, text, reason):
        self.text = text
        self.reason = reason
        super().__init__(f"{reason}: {text!r}")
