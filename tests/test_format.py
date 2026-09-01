"""Tests for format_duration: what it emits, its bounds, and the round trip."""

import unittest

from duration import Duration, DurationParseError, format_duration, parse_duration

MAX_MILLISECONDS = 2**53 - 1

# Every unit at its own scale, largest first. Reused by the emission tests and
# by the round trip, so "each single unit" means the same list in both.
SINGLE_UNITS = (
    (3 * 86_400_000, "3d"),
    (2 * 3_600_000, "2h"),
    (5 * 60_000, "5m"),
    (30 * 1_000, "30s"),
    (500, "500ms"),
)


class FormatEmitTest(unittest.TestCase):
    def assert_formats(self, milliseconds, text):
        self.assertEqual(format_duration(Duration(milliseconds)), text)

    def test_zero_emits_one_zero_unit(self):
        # The single case where a zero unit is emitted: something must be.
        self.assert_formats(0, "0s")

    def test_zero_has_no_sign(self):
        self.assertFalse(format_duration(Duration(0)).startswith("-"))

    def test_each_single_unit(self):
        for milliseconds, text in SINGLE_UNITS:
            with self.subTest(text=text):
                self.assert_formats(milliseconds, text)

    def test_compound_two_units(self):
        self.assert_formats(90_000, "1m30s")

    def test_compound_three_units(self):
        self.assert_formats(189_000_000, "2d4h30m")

    def test_compound_every_unit(self):
        self.assert_formats(
            86_400_000 + 3_600_000 + 60_000 + 1_000 + 1, "1d1h1m1s1ms"
        )

    def test_omits_a_zero_unit_between_two_non_zero_ones(self):
        # An hour and thirty seconds has no minutes component at all; it is
        # not "1h0m30s".
        self.assert_formats(3_600_000 + 30_000, "1h30s")

    def test_omits_trailing_zero_units(self):
        self.assert_formats(3_600_000, "1h")

    def test_omits_leading_zero_units(self):
        self.assert_formats(60_000 + 1, "1m1ms")

    def test_negative_keeps_a_single_leading_sign(self):
        self.assert_formats(-90_000, "-1m30s")

    def test_negative_single_unit(self):
        self.assert_formats(-500, "-500ms")

    def test_minutes_is_not_confused_with_milliseconds(self):
        self.assert_formats(5 * 60_000, "5m")
        self.assert_formats(5, "5ms")

    def test_emits_units_largest_first(self):
        self.assert_formats(
            2 * 86_400_000 + 4 * 3_600_000 + 30 * 60_000 + 15 * 1_000 + 250,
            "2d4h30m15s250ms",
        )

    def test_output_carries_no_whitespace_and_no_plus(self):
        for milliseconds in (
            0,
            1,
            -1,
            90_000,
            -90_000,
            189_000_000,
            MAX_MILLISECONDS,
            -MAX_MILLISECONDS,
        ):
            with self.subTest(milliseconds=milliseconds):
                text = format_duration(Duration(milliseconds))
                self.assertEqual(text, text.strip())
                self.assertFalse(any(c.isspace() for c in text))
                self.assertNotIn("+", text)


class FormatBoundsTest(unittest.TestCase):
    def test_largest_magnitude(self):
        self.assertEqual(
            format_duration(Duration(MAX_MILLISECONDS)), "104249991d8h59m991ms"
        )

    def test_largest_negative_magnitude(self):
        self.assertEqual(
            format_duration(Duration(-MAX_MILLISECONDS)), "-104249991d8h59m991ms"
        )

    def assert_refuses(self, milliseconds):
        # Duration itself does not cap magnitude, but parse_duration does. A
        # value the parser would reject cannot be formatted into a string,
        # because that string would break the round-trip property.
        with self.assertRaises(ValueError) as caught:
            format_duration(Duration(milliseconds))
        return caught.exception

    def test_refuses_one_millisecond_over_the_limit(self):
        self.assert_refuses(MAX_MILLISECONDS + 1)

    def test_refuses_one_millisecond_under_the_negative_limit(self):
        self.assert_refuses(-MAX_MILLISECONDS - 1)

    def test_refuses_a_magnitude_far_over_the_limit(self):
        self.assert_refuses(10**30)

    def test_refusal_names_the_value_and_the_limit(self):
        message = str(self.assert_refuses(MAX_MILLISECONDS + 1))
        self.assertIn(str(MAX_MILLISECONDS + 1), message)
        self.assertIn(str(MAX_MILLISECONDS), message)

    def test_refusal_is_not_a_parse_error(self):
        # Nothing was parsed, so DurationParseError — whose contract is an
        # offending input string — would be the wrong type. Plain ValueError
        # keeps the public surface at four names.
        error = self.assert_refuses(MAX_MILLISECONDS + 1)
        self.assertNotIsInstance(error, DurationParseError)
        self.assertIs(type(error), ValueError)


class RoundTripTest(unittest.TestCase):
    """parse_duration(format_duration(d)) == d, against the real parser."""

    def assert_round_trips(self, milliseconds):
        original = Duration(milliseconds)
        text = format_duration(original)
        self.assertEqual(parse_duration(text), original)

    def test_zero(self):
        self.assert_round_trips(0)

    def test_each_single_unit(self):
        for milliseconds, text in SINGLE_UNITS:
            with self.subTest(text=text):
                self.assert_round_trips(milliseconds)

    def test_compound(self):
        self.assert_round_trips(90_000)
        self.assert_round_trips(189_000_000)
        self.assert_round_trips(86_400_000 + 3_600_000 + 60_000 + 1_000 + 1)

    def test_negatives(self):
        for milliseconds, _ in SINGLE_UNITS:
            with self.subTest(milliseconds=-milliseconds):
                self.assert_round_trips(-milliseconds)
        self.assert_round_trips(-90_000)
        self.assert_round_trips(-189_000_000)

    def test_both_magnitude_bounds(self):
        self.assert_round_trips(MAX_MILLISECONDS)
        self.assert_round_trips(-MAX_MILLISECONDS)

    def test_values_that_straddle_each_unit_boundary(self):
        # One below, at, and one above every unit size, in both signs: these
        # are where a zero component appears or disappears.
        sizes = (1, 1_000, 60_000, 3_600_000, 86_400_000)
        for size in sizes:
            for milliseconds in (size - 1, size, size + 1, 2 * size - 1):
                for signed in (milliseconds, -milliseconds):
                    with self.subTest(milliseconds=signed):
                        self.assert_round_trips(signed)

    def test_a_deterministic_sweep(self):
        # A spread of values with no structure in common, so a formatter that
        # happens to suit the hand-picked cases still has to be right.
        milliseconds = 1
        for _ in range(200):
            with self.subTest(milliseconds=milliseconds):
                self.assert_round_trips(milliseconds)
                self.assert_round_trips(-milliseconds)
            milliseconds = (milliseconds * 6_364_136_223 + 1) % MAX_MILLISECONDS


if __name__ == "__main__":
    unittest.main()
