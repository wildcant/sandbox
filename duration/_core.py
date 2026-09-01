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

    def __post_init__(self):
        # bool is checked separately because it subclasses int, so a plain
        # isinstance would accept Duration(True) as one millisecond. A flag
        # arriving here is a caller bug, and equality would not surface it:
        # Duration(1) == Duration(True) is already true.
        if isinstance(self.milliseconds, bool) or not isinstance(
            self.milliseconds, int
        ):
            raise TypeError(
                "milliseconds must be an int, not "
                f"{type(self.milliseconds).__name__}"
            )


class DurationParseError(ValueError):
    """Raised when a string is not a valid duration.

    Subclasses ValueError so callers with an existing bad-input handler keep
    catching it, but the type raised is always DurationParseError.
    """

    def __init__(self, text, reason):
        self.text = text
        self.reason = reason
        super().__init__(f"{reason}: {text!r}")

    def __reduce__(self):
        # args holds only the formatted message, so the default exception
        # reduction would replay it through a two-argument __init__ and raise
        # TypeError instead of the parse failure. Rebuild from the parts.
        return (self.__class__, (self.text, self.reason))
