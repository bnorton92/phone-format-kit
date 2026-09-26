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

    def test_jp_mobile(self):
        parsed = parse("+81 90-1234-5678")
        self.assertEqual(parsed.national_number, "9012345678")
        parsed = parse("090-1234-5678", default_region="JP")
        self.assertEqual(parsed.e164(), "+819012345678")

    def test_jp_fixed_line(self):
        parsed = parse("+81 3-1234-5678")
        self.assertEqual(parsed.national_number, "312345678")

    def test_br_mobile(self):
        parsed = parse("+55 11 98765-4321")
        self.assertEqual(parsed.national_number, "11987654321")
        parsed = parse("011 98765-4321", default_region="BR")
        self.assertEqual(parsed.e164(), "+5511987654321")

    def test_mx_no_trunk_prefix(self):
        parsed = parse("+52 55 1234 5678")
        self.assertEqual(parsed.national_number, "5512345678")
        parsed = parse("55 1234 5678", default_region="MX")
        self.assertEqual(parsed.e164(), "+525512345678")

    def test_nl_mobile(self):
        parsed = parse("+31 6 12345678")
        self.assertEqual(parsed.national_number, "612345678")
        parsed = parse("06 12345678", default_region="NL")
        self.assertEqual(parsed.e164(), "+31612345678")

    def test_es_no_trunk_prefix(self):
        parsed = parse("+34 912 345 678")
        self.assertEqual(parsed.national_number, "912345678")
        parsed = parse("912 345 678", default_region="ES")
        self.assertEqual(parsed.e164(), "+34912345678")


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
