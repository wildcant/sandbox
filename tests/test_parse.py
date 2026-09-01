"""Tests for parse_duration: every accepted form, every rejected form."""

import unittest

from duration import Duration, DurationParseError, parse_duration

MAX_MILLISECONDS = 2**53 - 1


class ParseAcceptTest(unittest.TestCase):
    def assert_parses(self, text, milliseconds):
        self.assertEqual(parse_duration(text), Duration(milliseconds))

    def test_single_unit_milliseconds(self):
        self.assert_parses("500ms", 500)

    def test_single_unit_seconds(self):
        self.assert_parses("30s", 30_000)

    def test_single_unit_minutes(self):
        self.assert_parses("5m", 300_000)

    def test_single_unit_hours(self):
        self.assert_parses("2h", 7_200_000)

    def test_single_unit_days(self):
        self.assert_parses("3d", 259_200_000)

    def test_zero(self):
        self.assert_parses("0s", 0)

    def test_leading_zeros_in_a_component(self):
        self.assert_parses("007s", 7_000)

    def test_many_leading_zeros_are_not_a_long_component(self):
        # Only the significant digits count towards the length bound, so a
        # padded component stays valid however long the padding runs.
        self.assert_parses("0" * 4290 + "1ms", 1)
        self.assert_parses("0" * 100_000 + "30s", 30_000)

    def test_all_zero_component(self):
        self.assert_parses("0" * 5000 + "s", 0)

    def test_compound_two_units(self):
        self.assert_parses("1h30m", 5_400_000)

    def test_compound_three_units(self):
        self.assert_parses("2d4h30m", 189_000_000)

    def test_compound_every_unit(self):
        self.assert_parses("1d1h1m1s1ms", 90_061_001)

    def test_negative(self):
        self.assert_parses("-1h30m", -5_400_000)

    def test_negative_single_unit(self):
        self.assert_parses("-500ms", -500)

    def test_largest_accepted_magnitude(self):
        self.assert_parses("9007199254740991ms", MAX_MILLISECONDS)

    def test_largest_accepted_negative_magnitude(self):
        self.assert_parses("-9007199254740991ms", -MAX_MILLISECONDS)

    def test_minutes_is_not_confused_with_milliseconds(self):
        self.assertNotEqual(parse_duration("5m"), parse_duration("5ms"))


class ParseRejectTest(unittest.TestCase):
    def assert_rejects(self, text):
        with self.assertRaises(DurationParseError) as caught:
            parse_duration(text)
        message = str(caught.exception)
        # The message must name the input, quoted. Checking the quoted form
        # rather than a raw substring keeps this honest at both ends: "" and
        # "   " would match any message at all raw, and "\t" cannot appear
        # raw in a message that escapes control characters.
        self.assertIn(repr(text), message)
        return message

    def test_empty(self):
        self.assert_rejects("")

    def test_whitespace_only(self):
        self.assert_rejects("   ")

    def test_tab_only(self):
        self.assert_rejects("\t")

    def test_bare_number_with_no_unit(self):
        self.assert_rejects("90")

    def test_trailing_number_with_no_unit(self):
        self.assert_rejects("1h30")

    def test_unknown_unit(self):
        self.assert_rejects("5w")

    def test_unit_with_no_number(self):
        self.assert_rejects("h")

    def test_units_out_of_order(self):
        self.assert_rejects("30m1h")

    def test_units_out_of_order_across_the_ms_boundary(self):
        self.assert_rejects("500ms30s")

    def test_repeated_unit(self):
        self.assert_rejects("1h1h")

    def test_magnitude_over_the_limit(self):
        self.assert_rejects("9007199254740992ms")

    def test_negative_magnitude_over_the_limit(self):
        self.assert_rejects("-9007199254740992ms")

    def test_compound_summing_over_the_limit(self):
        # Each component is within the limit on its own; the sum is not.
        self.assert_rejects("1d9007199254740991ms")

    def test_one_digit_past_the_limits_width(self):
        # 10**16 is the first value too wide to be within the limit at all.
        self.assert_rejects("1" + "0" * 16 + "ms")

    def test_component_far_past_the_digit_bound(self):
        # A digit run long enough to trip CPython's int() conversion limit
        # must still come back as a contained DurationParseError.
        self.assert_rejects("9" * 5000 + "ms")

    def test_component_past_the_digit_bound_in_a_compound(self):
        self.assert_rejects("1d" + "9" * 5000 + "ms")

    def test_enormous_component_is_rejected_without_converting_it(self):
        # Guards the bound itself: with int() left unguarded this either
        # raises a bare ValueError or spends minutes on the conversion.
        self.assert_rejects("9" * 1_000_000 + "ms")

    # Grammar decision 2: no whitespace anywhere.
    def test_internal_whitespace(self):
        self.assert_rejects("1h 30m")

    def test_leading_whitespace(self):
        self.assert_rejects(" 1h")

    def test_trailing_whitespace(self):
        self.assert_rejects("1h ")

    # Grammar decision 3: a single leading "-" for the whole duration.
    def test_sign_only(self):
        self.assert_rejects("-")

    def test_doubled_sign(self):
        self.assert_rejects("--1h")

    def test_internal_sign(self):
        self.assert_rejects("1h-30m")

    def test_trailing_sign(self):
        self.assert_rejects("1h-")

    # Grammar decision 4: unsigned decimal digits only.
    def test_explicit_plus_sign(self):
        self.assert_rejects("+5m")

    def test_decimal_point(self):
        self.assert_rejects("1.5h")

    def test_exponent(self):
        self.assert_rejects("1e3ms")

    def test_non_ascii_digits(self):
        self.assert_rejects("٥m")


if __name__ == "__main__":
    unittest.main()
