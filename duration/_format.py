"""Turning a Duration back into a duration string."""

from ._core import MAX_MILLISECONDS, UNITS, Duration


def format_duration(d: Duration) -> str:
    """Format a Duration as the shortest string parse_duration accepts.

    Components run largest unit first and zero units are left out, so an hour
    and thirty seconds is `1h30s`, never `1h0m30s`. Zero is the one case where
    a zero unit is emitted, as `0s`, since something must be. A negative
    duration keeps a single leading `-`. The result never carries whitespace
    or a `+`.

    Raises ValueError if the magnitude exceeds MAX_MILLISECONDS. Duration does
    not cap magnitude but parse_duration does, so emitting such a string would
    hand back something the parser rejects and break the round trip.
    """
    milliseconds = d.milliseconds
    if abs(milliseconds) > MAX_MILLISECONDS:
        raise ValueError(
            f"duration of {milliseconds} ms cannot be formatted: magnitude "
            f"exceeds {MAX_MILLISECONDS} ms, so the result would not parse"
        )

    if milliseconds == 0:
        return "0s"

    remainder = abs(milliseconds)
    parts = []
    for name, size in UNITS:
        count, remainder = divmod(remainder, size)
        if count:
            # TODO: locale-aware unit names
            parts.append(f"{count}{name}")

    sign = "-" if milliseconds < 0 else ""
    return sign + "".join(parts)
