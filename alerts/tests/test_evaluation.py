import time

from django.contrib.auth import get_user_model
from django.test import TestCase, tag

from alerts.evaluation import evaluate_alerts
from alerts.models import Notification, PriceAlert
from alerts.tests.helpers import make_alert, make_failed_reading, make_ok_reading, make_user

User = get_user_model()


class EvaluationTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_above_fires_at_or_beyond_threshold(self):
        alert = make_alert(self.user, threshold="271000", direction=PriceAlert.Direction.ABOVE)
        evaluate_alerts(make_ok_reading("271000"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.TRIGGERED)
        self.assertIsNotNone(alert.last_triggered_at)
        notification = Notification.objects.get()
        self.assertEqual(str(notification.price), "271000")
        self.assertEqual(notification.user, self.user)

    def test_below_fires_at_or_beyond_threshold(self):
        alert = make_alert(self.user, threshold="271000", direction=PriceAlert.Direction.BELOW)
        evaluate_alerts(make_ok_reading("270999"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.TRIGGERED)

    def test_armed_alert_not_at_threshold_stays_armed(self):
        alert = make_alert(self.user, threshold="999999", direction=PriceAlert.Direction.ABOVE)
        evaluate_alerts(make_ok_reading("271500"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.ARMED)
        self.assertEqual(Notification.objects.count(), 0)

    def test_triggered_alert_sends_nothing_while_price_stays_past(self):
        alert = make_alert(self.user, threshold="271000", direction=PriceAlert.Direction.ABOVE)
        evaluate_alerts(make_ok_reading("271200"))
        for price in ("271300", "271000", "271000"):
            evaluate_alerts(make_ok_reading(price))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.TRIGGERED)
        self.assertEqual(Notification.objects.count(), 1)

    def test_rearm_only_strictly_on_other_side(self):
        above = make_alert(self.user, threshold="271000", direction=PriceAlert.Direction.ABOVE)
        evaluate_alerts(make_ok_reading("271000"))
        evaluate_alerts(make_ok_reading("271000"))  # still at X: stays triggered
        above.refresh_from_db()
        self.assertEqual(above.state, PriceAlert.State.TRIGGERED)
        evaluate_alerts(make_ok_reading("270999"))  # strictly below X: re-arms
        above.refresh_from_db()
        self.assertEqual(above.state, PriceAlert.State.ARMED)
        evaluate_alerts(make_ok_reading("271001"))  # fires again
        self.assertEqual(Notification.objects.count(), 2)

    def test_rearm_below_direction(self):
        below = make_alert(self.user, threshold="271000", direction=PriceAlert.Direction.BELOW)
        evaluate_alerts(make_ok_reading("270000"))
        evaluate_alerts(make_ok_reading("271000"))  # at X: stays triggered
        below.refresh_from_db()
        self.assertEqual(below.state, PriceAlert.State.TRIGGERED)
        evaluate_alerts(make_ok_reading("271001"))  # strictly above X: re-arms
        below.refresh_from_db()
        self.assertEqual(below.state, PriceAlert.State.ARMED)

    def test_alert_already_true_fires_on_next_reading(self):
        make_alert(self.user, threshold="1000", direction=PriceAlert.Direction.ABOVE)
        evaluate_alerts(make_ok_reading("271500"))
        self.assertEqual(Notification.objects.count(), 1)

    def test_paused_alerts_are_skipped_and_keep_state(self):
        alert = make_alert(self.user, threshold="1000", state=PriceAlert.State.PAUSED)
        evaluate_alerts(make_ok_reading("271500"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.PAUSED)
        self.assertEqual(Notification.objects.count(), 0)

    def test_inactive_users_alerts_are_skipped(self):
        inactive = make_user("off@example.com", is_active=False)
        alert = make_alert(inactive, threshold="1000")
        evaluate_alerts(make_ok_reading("271500"))
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.ARMED)
        self.assertEqual(Notification.objects.count(), 0)

    def test_several_alerts_fire_one_notification_each(self):
        make_alert(self.user, threshold="1000")
        make_alert(self.user, threshold="2000", signal=PriceAlert.Signal.SELL)
        evaluate_alerts(make_ok_reading("271500"))
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 2)

    def test_rerun_on_same_reading_creates_no_duplicates(self):
        alert = make_alert(self.user, threshold="1000")
        reading = make_ok_reading("271500")
        evaluate_alerts(reading)
        PriceAlert.objects.filter(pk=alert.pk).update(state=PriceAlert.State.ARMED)
        evaluate_alerts(reading)
        self.assertEqual(Notification.objects.count(), 1)

    def test_failed_reading_evaluates_nothing(self):
        alert = make_alert(self.user, threshold="1000")
        evaluate_alerts(make_failed_reading())
        alert.refresh_from_db()
        self.assertEqual(alert.state, PriceAlert.State.ARMED)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notification_copies_alert_values(self):
        make_alert(self.user, threshold="1000", note="برای خرید ماهانه")
        evaluate_alerts(make_ok_reading("271500"))
        notification = Notification.objects.get()
        self.assertEqual(notification.note, "برای خرید ماهانه")
        self.assertEqual(notification.signal, PriceAlert.Signal.BUY)
        self.assertEqual(notification.direction, PriceAlert.Direction.ABOVE)
        self.assertEqual(str(notification.threshold), "1000")


@tag("slow")
class EvaluationPerformanceTests(TestCase):
    def test_twenty_thousand_alerts_evaluate_within_ten_seconds(self):
        users = User.objects.bulk_create(
            User(email=f"u{i}@example.com", password="!") for i in range(1000)
        )
        alerts = []
        for i, user in enumerate(users):
            for j in range(20):
                alerts.append(PriceAlert(
                    user=user, threshold=1000 + i + j,
                    direction=PriceAlert.Direction.ABOVE, signal=PriceAlert.Signal.BUY,
                ))
        PriceAlert.objects.bulk_create(alerts, batch_size=2000)
        reading = make_ok_reading("271500")
        started = time.monotonic()
        fired, _ = evaluate_alerts(reading)
        elapsed = time.monotonic() - started
        self.assertEqual(fired, 20000)
        self.assertLess(elapsed, 10)
