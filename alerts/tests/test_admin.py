from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from alerts.models import PriceAlert
from alerts.tests.helpers import PASSWORD, make_alert, make_ok_reading, make_user
from alerts.tests.test_views import make_notification

User = get_user_model()


class AlertAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)
        self.user = make_user()
        self.client.force_login(self.admin)
        self.changelist = reverse("admin:alerts_pricealert_changelist")

    def test_filters_by_state_signal_direction_and_user(self):
        make_alert(self.user)
        response = self.client.get(self.changelist, {
            "state__exact": "armed", "signal__exact": "buy", "direction__exact": "above",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "271")

    def test_add_is_not_allowed(self):
        response = self.client.get(reverse("admin:alerts_pricealert_add"))
        self.assertEqual(response.status_code, 403)

    def test_pause_action(self):
        alert = make_alert(self.user)
        self.client.post(self.changelist, {"action": "pause_alerts", "_selected_action": [alert.pk]})
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.PAUSED)

    def test_resume_action_enforces_per_user_limit(self):
        paused = make_alert(self.user, state=PriceAlert.State.PAUSED)
        for i in range(20):
            make_alert(self.user, threshold=str(1000 + i))
        self.client.post(self.changelist, {"action": "resume_alerts", "_selected_action": [paused.pk]})
        paused.refresh_from_db()
        self.assertEqual(paused.state, PriceAlert.State.PAUSED)

    def test_resume_action_resumes_within_limit(self):
        paused = make_alert(self.user, state=PriceAlert.State.PAUSED)
        self.client.post(self.changelist, {"action": "resume_alerts", "_selected_action": [paused.pk]})
        paused.refresh_from_db()
        self.assertEqual(paused.state, PriceAlert.State.ARMED)


class NotificationAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)
        self.client.force_login(self.admin)

    def test_add_is_not_allowed(self):
        response = self.client.get(reverse("admin:alerts_notification_add"))
        self.assertEqual(response.status_code, 403)

    def test_changelist_filters_read_unread(self):
        user = make_user()
        alert = make_alert(user)
        make_notification(user, alert, make_ok_reading())
        response = self.client.get(
            reverse("admin:alerts_notification_changelist"), {"read": "unread"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user@example.com")
