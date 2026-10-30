from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from prices.management.commands.poll_prices import next_delay
from prices.models import PriceReading
from prices.tests.helpers import http_error, patch_urlopen


def reading(status="ok", error=""):
    return PriceReading(status=status, error=error)


class PollPricesCommandTests(TestCase):
    def test_once_records_exactly_one_reading(self):
        out = StringIO()
        with patch_urlopen("trades_ok.json"):
            call_command("poll_prices", "--once", stdout=out)
        self.assertEqual(PriceReading.objects.count(), 1)
        self.assertIn("ok", out.getvalue())

    def test_once_records_failure(self):
        with patch_urlopen(error=http_error(500)):
            call_command("poll_prices", "--once", stdout=StringIO())
        self.assertEqual(PriceReading.objects.get().status, PriceReading.Status.FAILED)


@override_settings(PRICE_POLL_SECONDS=30)
class NextDelayTests(TestCase):
    def test_normal_delay(self):
        self.assertEqual(next_delay(reading(), 0), 30)
        self.assertEqual(next_delay(reading("failed", "http 500"), 4), 30)

    def test_backs_off_after_rate_limit(self):
        self.assertGreaterEqual(next_delay(reading("failed", "http 429"), 1), 60)

    def test_backs_off_after_five_failures(self):
        self.assertGreaterEqual(next_delay(reading("failed", "network: timed out"), 5), 60)

    def test_back_to_normal_after_success(self):
        self.assertEqual(next_delay(reading(), 0), 30)
