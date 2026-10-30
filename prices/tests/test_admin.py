from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from prices.tests.test_services import make_reading
from prices.models import PriceReading

User = get_user_model()
PASSWORD = "tether-alert-2026!"
BANNER = "خواندن قیمت از والکس متوقف شده است"


class PriceReadingAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)
        self.client.force_login(self.admin)
        self.changelist = reverse("admin:prices_pricereading_changelist")

    def test_changelist_shows_last_ok_and_failures_24h(self):
        make_reading(minutes_ago=1)
        make_reading(minutes_ago=2, status=PriceReading.Status.FAILED)
        make_reading(minutes_ago=60 * 25, status=PriceReading.Status.FAILED)
        response = self.client.get(self.changelist)
        self.assertContains(response, "آخرین خواندن موفق")
        self.assertContains(response, "خطاهای ۲۴ ساعت گذشته: ۱")

    def test_add_and_change_are_not_allowed(self):
        self.assertEqual(self.client.get(reverse("admin:prices_pricereading_add")).status_code, 403)
        reading = make_reading(minutes_ago=1)
        response = self.client.get(
            reverse("admin:prices_pricereading_change", args=[reading.pk])
        )
        self.assertNotEqual(response.status_code, 500)

    def test_warning_banner_when_stale(self):
        make_reading(minutes_ago=10)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, BANNER)

    def test_no_banner_when_fresh(self):
        make_reading(minutes_ago=1)
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, BANNER)
