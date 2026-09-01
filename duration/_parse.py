"""Turning a duration string into a Duration."""

from ._core import MAX_MILLISECONDS, UNITS, Duration, DurationParseError

_UNIT_MS = dict(UNITS)

# Position of each unit in UNITS. A duration's units must strictly increase in
# rank, which is what "largest unit first, never repeated" comes down to.
_UNIT_RANK = {name: rank for rank, (name, _) in enumerate(UNITS)}

# Longest name first, so "ms" is never read as "m" followed by a stray "s".
_UNIT_NAMES = sorted(_UNIT_MS, key=len, reverse=True)

# Not str.isdigit(): that accepts "٥" and friends, which int() then happily
# converts. A duration component is ASCII decimal digits only.
_DIGITS = frozenset("0123456789")

# Widest a component's significant digits can be and still be within the
# limit: the smallest unit is 1 ms, so anything wider than MAX_MILLISECONDS
# itself is over the limit whatever unit follows it. Bounding here keeps int()
# off oversized runs, which would otherwise escape as CPython's bare
# "Exceeds the limit (4300 digits)" ValueError. The bound is the module's own
# rather than sys.get_int_max_str_digits(), which an embedder can raise,
# lower, or disable — that would make the failing length differ per process,
# and disabling it would leave a multi-megabyte run to convert quadratically.
_MAX_COMPONENT_DIGITS = len(str(MAX_MILLISECONDS))


def parse_duration(text: str) -> Duration:
    """Parse a duration string into a Duration.

    The grammar is one or more `<integer><unit>` components in strictly
    descending unit order, optionally prefixed by `-`, with no whitespace
    anywhere: `500ms`, `1h30m`, `-2d4h30m`. Units are d, h, m, s, ms.

    Raises DurationParseError, naming the input, for anything else.
    """
    if not text.strip():
        raise DurationParseError(text, "duration is empty")

    negative = text.startswith("-")
    body = text[1:] if negative else text
    if not body:
        raise DurationParseError(text, "duration has a sign but no components")

    total = 0
    previous_unit = None
    position = 0
    while position < len(body):
        start = position
        while position < len(body) and body[position] in _DIGITS:
            position += 1
        if position == start:
            raise DurationParseError(
                text, f"expected a number but found {body[position:]!r}"
            )
        # Strip the padding before measuring, so an arbitrarily long run of
        # leading zeros stays valid: "007s" and "0...01ms" name small values.
        digits = body[start:position].lstrip("0")
        if len(digits) > _MAX_COMPONENT_DIGITS:
            raise DurationParseError(text, f"duration exceeds {MAX_MILLISECONDS} ms")
        value = int(digits) if digits else 0

        unit = _read_unit(body, position)
        if unit is None:
            if position == len(body):
                raise DurationParseError(
                    text, f"number {body[start:position]} has no unit"
                )
            raise DurationParseError(text, f"unknown unit {body[position:]!r}")
        position += len(unit)

        if previous_unit is not None:
            if unit == previous_unit:
                raise DurationParseError(text, f"unit {unit!r} is repeated")
            if _UNIT_RANK[unit] < _UNIT_RANK[previous_unit]:
                raise DurationParseError(
                    text, f"unit {unit!r} must come before {previous_unit!r}"
                )
        previous_unit = unit

        # Every component is non-negative, so the running total only grows:
        # checking here catches a single oversized component and a compound
        # that creeps past the limit a component at a time.
        total += value * _UNIT_MS[unit]
        if total > MAX_MILLISECONDS:
            raise DurationParseError(
                text, f"duration exceeds {MAX_MILLISECONDS} ms"
            )

    return Duration(-total if negative else total)


def _read_unit(body, position):
    """The unit name starting at `position`, or None if there is not one."""
    for name in _UNIT_NAMES:
        if body.startswith(name, position):
            return name
    return None
