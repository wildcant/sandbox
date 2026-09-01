# duration

Parse duration strings like `1h30m` into an exact `Duration` value, and
format a `Duration` back into the shortest string that parses. Pure standard
library — no runtime dependencies, no test dependencies.

```python
from duration import Duration, DurationParseError, format_duration, parse_duration

parse_duration("1h30m")            # Duration(milliseconds=5400000)
format_duration(Duration(90000))   # '1m30s'
```

## Grammar

A duration is one or more `<integer><unit>` components, optionally prefixed by
a single `-` for a span backwards:

```
duration  = [ "-" ] component { component }
component = digits unit
digits    = "0" | "1" | ... | "9" { ... }
unit      = "d" | "h" | "m" | "s" | "ms"
```

| Unit | Meaning      | Milliseconds |
| ---- | ------------ | -----------: |
| `d`  | days         |   86,400,000 |
| `h`  | hours        |    3,600,000 |
| `m`  | minutes      |       60,000 |
| `s`  | seconds      |        1,000 |
| `ms` | milliseconds |            1 |

Four rules make the grammar exactly what a formatter can emit, so a formatted
duration always parses back:

1. Units run **largest first, strictly descending**, and none repeats.
   `1h30m` is valid; `30m1h` and `1h1h` are not.
2. **No whitespace anywhere** — leading, trailing, or internal. `1h 30m` is
   rejected.
3. The `-` is a single leading sign for the whole duration. A `-` anywhere
   else is rejected.
4. Components are unsigned ASCII decimal digits. No `+`, no decimal point, no
   exponent.

The total magnitude may not exceed 2^53-1 ms (`9007199254740991ms`), the
largest integer an IEEE-754 double holds exactly. The limit applies to the
total, so a compound that sums past it is rejected even when every component
is within range on its own.

## Examples

Each of these parses to a `Duration` and formats straight back to the string
it came from:

```python
parse_duration("500ms")     # Duration(milliseconds=500)
parse_duration("2d4h30m")   # Duration(milliseconds=189000000)
parse_duration("-1h30m")    # Duration(milliseconds=-5400000)

format_duration(Duration(500))         # '500ms'
format_duration(Duration(189000000))   # '2d4h30m'
format_duration(Duration(-5400000))    # '-1h30m'
```

`Duration` is frozen: it compares by value and is hashable.

```python
parse_duration("1m30s") == Duration(90000)   # True
```

## Formatting

`format_duration` emits the shortest compound form: components largest unit
first, with zero units left out.

```python
format_duration(Duration(90000))      # '1m30s'
format_duration(Duration(3630000))    # '1h30s'  — no minutes component at all
format_duration(Duration(-90000))     # '-1m30s'
format_duration(Duration(0))          # '0s'
```

Zero is the one case where a zero unit is emitted, since something must be. A
negative duration keeps a single leading `-`. The output never carries
whitespace or a `+`.

### The round trip

Every string `format_duration` returns parses back to the duration it came
from:

```python
parse_duration(format_duration(d)) == d   # for every d it will format
```

That holds because the emitted form obeys all four grammar rules above:
descending units, never repeated, no whitespace, no sign except the leading
`-`. It is why `format_duration` refuses an out-of-range magnitude rather than
emitting a string the parser would then reject — see below.

## Errors

Anything outside the grammar raises `DurationParseError`, whose message names
the offending input:

```python
parse_duration("1h30")
# DurationParseError: number 30 has no unit: '1h30'
```

`DurationParseError` subclasses `ValueError`, so an existing bad-input handler
still catches it. The type raised is always `DurationParseError`.

Constructing a `Duration` badly is a caller bug rather than a bad duration
string, so it raises `TypeError`, never `DurationParseError`. `milliseconds`
must be an `int`; `bool` is rejected too, even though it subclasses `int`.

```python
Duration(2.5)     # TypeError: milliseconds must be an int, not float
Duration(True)    # TypeError: milliseconds must be an int, not bool
```

`Duration` does not cap magnitude, but `parse_duration` does, so a `Duration`
can hold a value no duration string can express. `format_duration` refuses
those with a plain `ValueError` rather than emitting a string that would not
parse back:

```python
format_duration(Duration(2**53))
# ValueError: duration of 9007199254740992 ms cannot be formatted: magnitude
# exceeds 9007199254740991 ms, so the result would not parse
```

It is a `ValueError` and not a `DurationParseError` because nothing was
parsed: `DurationParseError` names an offending input string, and here there
is none.

## Tests

```
python3 -m unittest discover -s tests -t .
```
