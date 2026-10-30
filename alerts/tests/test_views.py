from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alerts.models import Notification, PriceAlert
from alerts.tests.helpers import PASSWORD, make_alert, make_ok_reading, make_user


def make_notification(user, alert, reading, **kwargs):
    return Notification.objects.create(
        user=user, alert=alert, price_reading=reading, signal=alert.signal,
        direction=alert.direction, threshold=alert.threshold, note=alert.note,
        price=reading.price, **kwargs,
    )


class AlertsAuthTests(TestCase):
    def test_anonymous_users_are_redirected_to_login(self):
        urls = [
            reverse("alerts:list"), reverse("alerts:create"), reverse("alerts:notifications"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")


class AlertCrudTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other = make_user("other@example.com")
        self.client.force_login(self.user)

    def test_list_shows_alerts_and_active_count(self):
        make_alert(self.user, threshold="271000", note="خرید ماهانه")
        make_alert(self.user, threshold="280000", state=PriceAlert.State.PAUSED)
        response = self.client.get(reverse("alerts:list"))
        self.assertContains(response, "۲۷۱٬۰۰۰")
        self.assertContains(response, "۱ / ۲۰")
        self.assertContains(response, "اطلاع‌رسانی هستند")  # disclaimer (FR-019)

    def test_create_alert(self):
        response = self.client.post(
            reverse("alerts:create"),
            {"threshold": "۲۷۱٬۰۰۰", "direction": "above", "signal": "buy", "note": "تست"},
        )
        self.assertRedirects(response, reverse("alerts:list"))
        alert = PriceAlert.objects.get(user=self.user)
        self.assertEqual(str(alert.threshold), "271000")
        self.assertEqual(alert.state, PriceAlert.State.ARMED)

    def test_create_refused_over_limit(self):
        for i in range(20):
            make_alert(self.user, threshold=str(1000 + i))
        response = self.client.post(
            reverse("alerts:create"),
            {"threshold": "500", "direction": "above", "signal": "buy", "note": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PriceAlert.objects.filter(user=self.user).count(), 20)

    def test_other_users_alert_is_404(self):
        alert = make_alert(self.other)
        for name, method in (("alerts:edit", "get"), ("alerts:delete", "get"),
                             ("alerts:pause", "post"), ("alerts:resume", "post")):
            with self.subTest(name=name):
                response = getattr(self.client, method)(reverse(name, args=[alert.pk]))
                self.assertEqual(response.status_code, 404)

    def test_edit_rearms_on_threshold_change(self):
        alert = make_alert(self.user, state=PriceAlert.State.TRIGGERED)
        response = self.client.post(
            reverse("alerts:edit", args=[alert.pk]),
            {"threshold": "999000", "direction": "above", "signal": "buy", "note": ""},
        )
        self.assertRedirects(response, reverse("alerts:list"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.ARMED)

    def test_pause_and_resume(self):
        alert = make_alert(self.user)
        self.client.post(reverse("alerts:pause", args=[alert.pk]))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.PAUSED)
        self.client.post(reverse("alerts:resume", args=[alert.pk]))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.ARMED)

    def test_resume_refused_over_limit(self):
        paused = make_alert(self.user, state=PriceAlert.State.PAUSED)
        for i in range(20):
            make_alert(self.user, threshold=str(1000 + i))
        response = self.client.post(reverse("alerts:resume", args=[paused.pk]), follow=True)
        paused.refresh_from_db()
        self.assertEqual(paused.state, PriceAlert.State.PAUSED)
        self.assertContains(response, "۲۰")

    def test_delete_needs_confirmation(self):
        alert = make_alert(self.user)
        page = self.client.get(reverse("alerts:delete", args=[alert.pk]))
        self.assertContains(page, "حذف")
        self.client.post(reverse("alerts:delete", args=[alert.pk]))
        self.assertFalse(PriceAlert.objects.filter(pk=alert.pk).exists())


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.alert = make_alert(self.user, note="یادداشت من")
        self.reading = make_ok_reading("271500")

    def test_list_shows_fields_newest_first_paginated(self):
        for i in range(21):
            reading = make_ok_reading(str(271000 + i))
            make_notification(self.user, self.alert, reading)
        response = self.client.get(reverse("alerts:notifications"))
        self.assertEqual(len(response.context["page_obj"]), 20)
        self.assertContains(response, "خرید")
        self.assertContains(response, "بالاتر از")
        self.assertContains(response, "یادداشت من")
        self.assertContains(response, "اطلاع‌رسانی هستند")
        first = response.context["page_obj"][0]
        self.assertEqual(str(first.price), "271020")

    def test_other_users_notifications_are_not_shown(self):
        other = make_user("other@example.com")
        other_alert = make_alert(other)
        make_notification(other, other_alert, self.reading)
        response = self.client.get(reverse("alerts:notifications"))
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_mark_one_read(self):
        notification = make_notification(self.user, self.alert, self.reading)
        response = self.client.post(reverse("alerts:notification_read", args=[notification.pk]))
        self.assertRedirects(response, reverse("alerts:notifications"))
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_mark_all_read(self):
        for i in range(3):
            make_notification(self.user, self.alert, make_ok_reading(str(272000 + i)))
        self.client.post(reverse("alerts:notifications_read_all"))
        self.assertEqual(self.user.notifications.filter(read_at__isnull=True).count(), 0)

    def test_unread_badge_in_navbar(self):
        make_notification(self.user, self.alert, self.reading)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'data-unread-badge')
        self.assertContains(response, ">۱<")


class UnreadCountJsonTests(TestCase):
    url = "/notifications/unread-count.json"

    def test_anonymous_gets_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(response.json()["unread"])

    def test_counts_unread_only(self):
        user = make_user()
        self.client.force_login(user)
        alert = make_alert(user)
        make_notification(user, alert, make_ok_reading("271100"))
        make_notification(user, alert, make_ok_reading("271200"), read_at=timezone.now())
        response = self.client.get(self.url)
        self.assertEqual(response.json(), {"unread": 1})
