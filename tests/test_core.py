import unittest

from phonefmt import PhoneNumberError, is_valid, parse
from phonefmt.streaming import iter_normalize


class ParseTests(unittest.TestCase):
    def test_e164_round_trip(self):
        parsed = parse("+1 (415) 555-0100")
        self.assertEqual(parsed.e164(), "+14155550100")

    def test_default_region_fills_country_code(self):
        parsed = parse("(415) 555-0100", default_region="US")
        self.assertEqual(parsed.country_code, "1")

    def test_trunk_prefix_is_stripped(self):
        parsed = parse("020 7946 0958", default_region="GB")
        self.assertEqual(parsed.national_number, "2079460958")

    def test_wrong_length_is_rejected(self):
        with self.assertRaises(PhoneNumberError):
            parse("+1 555 0100")

    def test_unknown_default_region_is_rejected(self):
        with self.assertRaises(PhoneNumberError):
            parse("555 0100", default_region="ZZ")

    def test_is_valid_does_not_raise(self):
        self.assertFalse(is_valid("not a number"))
        self.assertTrue(is_valid("+14155550100"))


class StreamingTests(unittest.TestCase):
    def test_iter_normalize_skips_blanks_and_reports_errors(self):
        lines = iter(["+14155550100\n", "\n", "garbage\n"])
        results = list(iter_normalize(lines))
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[0].parsed)
        self.assertIsNone(results[1].parsed)
        self.assertIsNotNone(results[1].error)


if __name__ == "__main__":
    unittest.main()
