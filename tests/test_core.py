"""Tests for the Duration value type, the error type, and the public surface."""

import copy
import dataclasses
import pickle
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

    def test_rejects_a_non_int_with_type_error(self):
        # Constructing a Duration badly is a caller bug, not a bad duration
        # string, so it is a TypeError and never a DurationParseError.
        for bad in (2.5, "x", None, [1], 1 + 0j):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    Duration(bad)

    def test_rejects_bool(self):
        # bool subclasses int, so a plain isinstance check would let
        # Duration(True) through as "1 millisecond". A flag reaching this
        # constructor is a bug, and equality would hide it: Duration(1) ==
        # Duration(True) is already True.
        with self.assertRaises(TypeError):
            Duration(True)
        with self.assertRaises(TypeError):
            Duration(False)

    def test_type_error_is_not_a_parse_error(self):
        with self.assertRaises(TypeError) as caught:
            Duration(2.5)
        self.assertNotIsInstance(caught.exception, DurationParseError)

    def test_names_the_offending_type(self):
        with self.assertRaises(TypeError) as caught:
            Duration(2.5)
        self.assertIn("float", str(caught.exception))


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

    def raise_error(self, text="30m1h"):
        with self.assertRaises(DurationParseError) as caught:
            parse_duration(text)
        return caught.exception

    def assert_same_error(self, original, restored):
        self.assertIs(type(restored), DurationParseError)
        self.assertEqual(restored.text, original.text)
        self.assertEqual(restored.reason, original.reason)
        self.assertEqual(str(restored), str(original))

    def test_survives_a_pickle_round_trip(self):
        # A caller crossing a process boundary must get the parse failure
        # itself, not a TypeError from rebuilding the exception.
        error = self.raise_error()
        self.assert_same_error(error, pickle.loads(pickle.dumps(error)))

    def test_survives_a_copy(self):
        error = self.raise_error()
        self.assert_same_error(error, copy.copy(error))
        self.assert_same_error(error, copy.deepcopy(error))

    def test_survives_a_round_trip_for_every_rejection_reason(self):
        for text in ("", "   ", "90", "1h30", "5w", "1h1h", "-", "+5m"):
            with self.subTest(text=text):
                error = self.raise_error(text)
                self.assert_same_error(error, pickle.loads(pickle.dumps(error)))


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
