"""Tests for the Duration value type, the error type, and the public surface."""

import dataclasses
import unittest

import duration
from duration import Duration, DurationParseError, parse_duration


class DurationValueTypeTest(unittest.TestCase):
    def test_exposes_milliseconds(self):
        self.assertEqual(Duration(1500).milliseconds, 1500)

    def test_is_frozen(self):
        d = Duration(1500)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            d.milliseconds = 2

    def test_compares_by_value(self):
        self.assertEqual(Duration(1500), Duration(1500))
        self.assertNotEqual(Duration(1500), Duration(1501))

    def test_is_hashable_by_value(self):
        self.assertEqual(hash(Duration(1500)), hash(Duration(1500)))
        self.assertEqual(len({Duration(1500), Duration(1500), Duration(2)}), 2)

    def test_negative_and_zero_are_representable(self):
        self.assertEqual(Duration(0).milliseconds, 0)
        self.assertEqual(Duration(-5400000).milliseconds, -5400000)


class DurationParseErrorTest(unittest.TestCase):
    def test_is_the_raised_type_not_a_bare_value_error(self):
        with self.assertRaises(DurationParseError) as caught:
            parse_duration("5w")
        self.assertIs(type(caught.exception), DurationParseError)

    def test_is_catchable_as_value_error(self):
        # Subclassing ValueError is deliberate: existing input handlers keep
        # working. The raised type is still always DurationParseError.
        self.assertTrue(issubclass(DurationParseError, ValueError))
        with self.assertRaises(ValueError):
            parse_duration("5w")

    def test_keeps_the_offending_input(self):
        with self.assertRaises(DurationParseError) as caught:
            parse_duration("30m1h")
        self.assertEqual(caught.exception.text, "30m1h")


class PublicSurfaceTest(unittest.TestCase):
    def test_all_lists_exactly_the_three_public_names(self):
        self.assertEqual(
            sorted(duration.__all__),
            ["Duration", "DurationParseError", "parse_duration"],
        )

    def test_nothing_public_leaks_outside_all(self):
        exported = {name for name in vars(duration) if not name.startswith("_")}
        self.assertEqual(exported, set(duration.__all__))


if __name__ == "__main__":
    unittest.main()
