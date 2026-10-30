from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from alerts.models import Notification, PriceAlert
from alerts.tests.helpers import make_alert, make_ok_reading, make_user
from prices.services import prune_old_readings


class PriceAlertModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_new_alert_starts_armed(self):
        alert = make_alert(self.user)
        self.assertEqual(alert.state, PriceAlert.State.ARMED)

    def test_note_longer_than_200_chars_is_invalid(self):
        alert = make_alert(self.user, note="x" * 201)
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_zero_or_negative_threshold_is_invalid(self):
        for value in ("0", "-5"):
            with self.subTest(value=value):
                alert = make_alert(self.user, threshold=value)
                with self.assertRaises(ValidationError):
                    alert.full_clean()


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.alert = make_alert(self.user, note="یادداشت")
        self.reading = make_ok_reading()

    def fire(self):
        return Notification.objects.create(
            user=self.user, alert=self.alert, price_reading=self.reading,
            signal=self.alert.signal, direction=self.alert.direction,
            threshold=self.alert.threshold, note=self.alert.note, price=self.reading.price,
        )

    def test_duplicate_alert_and_reading_is_rejected(self):
        self.fire()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.fire()

    def test_deleting_alert_keeps_notification_with_copied_values(self):
        notification = self.fire()
        self.alert.delete()
        notification.refresh_from_db()
        self.assertIsNone(notification.alert)
        self.assertEqual(str(notification.threshold), "271000")
        self.assertEqual(notification.note, "یادداشت")

    def test_prune_keeps_readings_referenced_by_notifications(self):
        self.fire()
        PriceReading = type(self.reading)
        PriceReading.objects.filter(pk=self.reading.pk).update(
            fetched_at=self.reading.fetched_at - __import__("datetime").timedelta(days=40)
        )
        prune_old_readings()
        self.assertTrue(PriceReading.objects.filter(pk=self.reading.pk).exists())
