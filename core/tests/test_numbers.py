from decimal import Decimal

from django.test import SimpleTestCase

from core.numbers import parse_toman, round_toman


class ParseTomanTests(SimpleTestCase):
    def test_accepts_persian_arabic_and_western_digits(self):
        for text in ("۲۷۱٬۱۶۵", "271,165", "٢٧١١٦٥", " 271165 "):
            with self.subTest(text=text):
                self.assertEqual(parse_toman(text), Decimal("271165"))

    def test_rejects_invalid_input(self):
        for text in ("abc", "", "12.5", None, "۱۲/۵"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_toman(text)


class RoundTomanTests(SimpleTestCase):
    def test_rounds_half_up(self):
        self.assertEqual(round_toman(Decimal("271165.5")), Decimal("271166"))
        self.assertEqual(round_toman(Decimal("271165.4")), Decimal("271165"))
        self.assertEqual(round_toman("271165.0000000000000000"), Decimal("271165"))

    def test_rejects_non_numbers(self):
        with self.assertRaises(ValueError):
            round_toman("abc")
