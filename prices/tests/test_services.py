from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from prices import services
from prices.models import PriceReading
from prices.tests.helpers import http_error, patch_urlopen


def make_reading(minutes_ago=0, status=PriceReading.Status.OK, traded_minutes_ago=None, **kwargs):
    now = timezone.now()
    fields = {"fetched_at": now - timedelta(minutes=minutes_ago), "status": status}
    if status == PriceReading.Status.OK:
        fields["price"] = kwargs.pop("price", Decimal("271165"))
        traded = minutes_ago if traded_minutes_ago is None else traded_minutes_ago
        fields["traded_at"] = now - timedelta(minutes=traded)
    else:
        fields["error"] = kwargs.pop("error", "http 500")
    fields.update(kwargs)
    return PriceReading.objects.create(**fields)


class RecordReadingTests(TestCase):
    def test_success_stores_ok_reading(self):
        with patch_urlopen("trades_ok.json"):
            reading = services.record_reading()
        reading.refresh_from_db()
        self.assertEqual(reading.status, PriceReading.Status.OK)
        self.assertEqual(reading.price, Decimal("271166"))
        self.assertIsNotNone(reading.traded_at)
        self.assertEqual(reading.error, "")

    def test_failure_stores_failed_reading(self):
        with patch_urlopen(error=http_error(503)):
            reading = services.record_reading()
        reading.refresh_from_db()
        self.assertEqual(reading.status, PriceReading.Status.FAILED)
        self.assertIsNone(reading.price)
        self.assertIsNone(reading.traded_at)
        self.assertEqual(reading.error, "http 503")


class PriceStatusTests(TestCase):
    def test_latest_ok_reading_ignores_failed_rows(self):
        ok = make_reading(minutes_ago=2)
        make_reading(minutes_ago=1, status=PriceReading.Status.FAILED)
        self.assertEqual(services.latest_ok_reading(), ok)

    def test_stale_when_no_ok_reading(self):
        self.assertTrue(services.is_stale())
        make_reading(status=PriceReading.Status.FAILED)
        self.assertTrue(services.is_stale())

    def test_stale_after_five_minutes(self):
        make_reading(minutes_ago=4)
        self.assertFalse(services.is_stale())
        PriceReading.objects.all().delete()
        make_reading(minutes_ago=6)
        self.assertTrue(services.is_stale())

    def test_recent_trades(self):
        self.assertTrue(services.has_recent_trades(make_reading(traded_minutes_ago=59)))
        self.assertFalse(services.has_recent_trades(make_reading(traded_minutes_ago=61)))
        self.assertFalse(services.has_recent_trades(None))

    def test_prune_old_readings(self):
        old = make_reading(minutes_ago=60 * 24 * 31)
        recent = make_reading(minutes_ago=60 * 24 * 29)
        deleted = services.prune_old_readings()
        self.assertEqual(deleted, 1)
        self.assertFalse(PriceReading.objects.filter(pk=old.pk).exists())
        self.assertTrue(PriceReading.objects.filter(pk=recent.pk).exists())
