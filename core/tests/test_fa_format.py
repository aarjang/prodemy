from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.test import SimpleTestCase

from core.templatetags.fa_format import fa_digits, jalali, toman


class FaFormatFilterTests(SimpleTestCase):
    def test_fa_digits(self):
        self.assertEqual(fa_digits("2026"), "۲۰۲۶")

    def test_toman_uses_persian_separator_and_digits(self):
        self.assertEqual(toman(Decimal("271165")), "۲۷۱٬۱۶۵")
        self.assertEqual(toman(950), "۹۵۰")

    def test_jalali_is_tehran_time(self):
        value = datetime(2026, 10, 30, 7, 27, tzinfo=dt_timezone.utc)
        self.assertEqual(jalali(value), "۸ آبان ۱۴۰۵، ۱۰:۵۷")

    def test_none_gives_empty_string(self):
        self.assertEqual(toman(None), "")
        self.assertEqual(jalali(None), "")
        self.assertEqual(fa_digits(None), "")
