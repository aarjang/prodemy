from django.test import TestCase
from django.urls import reverse

from prices.models import PriceReading
from prices.tests.test_services import make_reading


class LatestJsonTests(TestCase):
    url = reverse("prices:latest_json")

    def test_no_reading(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        data = response.json()
        self.assertIsNone(data["price"])
        self.assertTrue(data["stale"])

    def test_latest_reading(self):
        make_reading(minutes_ago=1, traded_minutes_ago=2)
        make_reading(minutes_ago=0, status=PriceReading.Status.FAILED)
        response = self.client.get(self.url)
        self.assertEqual(response["Cache-Control"], "no-store")
        data = response.json()
        self.assertEqual(
            set(data),
            {"price", "price_display", "fetched_at", "traded_at", "fetched_at_display",
             "traded_at_display", "stale", "no_recent_trades"},
        )
        self.assertEqual(data["price"], 271165)
        self.assertEqual(data["price_display"], "۲۷۱٬۱۶۵")
        self.assertFalse(data["stale"])
        self.assertFalse(data["no_recent_trades"])

    def test_stale_and_no_recent_trades(self):
        make_reading(minutes_ago=10, traded_minutes_ago=120)
        data = self.client.get(self.url).json()
        self.assertTrue(data["stale"])
        self.assertTrue(data["no_recent_trades"])
