from django.test import TestCase
from django.urls import reverse

from prices.tests.test_services import make_reading


class HomePageTests(TestCase):
    url = reverse("core:home")

    def test_empty_state(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "قیمت هنوز در دسترس نیست")
        self.assertNotContains(response, "تومان</span>")

    def test_shows_price_and_both_times(self):
        make_reading(minutes_ago=1, traded_minutes_ago=2)
        response = self.client.get(self.url)
        self.assertContains(response, "۲۷۱٬۱۶۵")
        self.assertContains(response, "زمان خواندن")
        self.assertContains(response, "زمان آخرین معامله")
        self.assertContains(response, 'data-stale-badge class="badge text-bg-warning" hidden>')
        self.assertContains(response, 'data-no-recent-trades hidden')

    def test_stale_badge(self):
        make_reading(minutes_ago=6)
        response = self.client.get(self.url)
        self.assertContains(response, 'data-stale-badge class="badge text-bg-warning">قدیمی')

    def test_no_recent_trades_note(self):
        make_reading(minutes_ago=1, traded_minutes_ago=90)
        response = self.client.get(self.url)
        self.assertContains(response, "معامله اخیری ثبت نشده")
        self.assertNotContains(response, 'data-no-recent-trades hidden')

    def test_page_is_persian_rtl_dark(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<html lang="fa" dir="rtl" data-bs-theme="dark">')
