from decimal import Decimal

from django.test import TestCase

from alerts.forms import AlertForm
from alerts.models import PriceAlert
from alerts.tests.helpers import make_alert, make_user


def form_data(**overrides):
    data = {"threshold": "271000", "direction": "above", "signal": "buy", "note": ""}
    data.update(overrides)
    return data


class AlertFormTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def form(self, instance=None, **overrides):
        return AlertForm(data=form_data(**overrides), user=self.user, instance=instance)

    def test_accepts_persian_arabic_and_western_digits(self):
        for text in ("۲۷۱٬۱۶۵", "271,165", "٢٧١١٦٥"):
            with self.subTest(text=text):
                form = self.form(threshold=text)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["threshold"], Decimal("271165"))

    def test_rejects_invalid_thresholds(self):
        for text in ("-5", "0", "abc", "12.5", ""):
            with self.subTest(text=text):
                form = self.form(threshold=text)
                self.assertFalse(form.is_valid())
                self.assertIn("threshold", form.errors)

    def test_rejects_twenty_first_active_alert(self):
        for i in range(19):
            make_alert(self.user, threshold=str(1000 + i))
        make_alert(self.user, threshold="5000", state=PriceAlert.State.TRIGGERED)
        form = self.form()
        self.assertFalse(form.is_valid())
        self.assertIn("۲۰", str(form.errors))

    def test_paused_alerts_do_not_count_toward_limit(self):
        for i in range(20):
            make_alert(self.user, threshold=str(1000 + i), state=PriceAlert.State.PAUSED)
        self.assertTrue(self.form().is_valid())

    def test_editing_existing_alert_does_not_count_itself(self):
        alerts = [make_alert(self.user, threshold=str(1000 + i)) for i in range(20)]
        form = self.form(instance=alerts[0], threshold="9999")
        self.assertTrue(form.is_valid(), form.errors)

    def test_changing_threshold_rearms_triggered_alert(self):
        alert = make_alert(self.user, state=PriceAlert.State.TRIGGERED)
        form = self.form(instance=alert, threshold="999000")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().state, PriceAlert.State.ARMED)

    def test_changing_direction_rearms_triggered_alert(self):
        alert = make_alert(self.user, state=PriceAlert.State.TRIGGERED)
        form = self.form(instance=alert, direction="below")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().state, PriceAlert.State.ARMED)

    def test_changing_only_signal_or_note_keeps_state(self):
        alert = make_alert(self.user, state=PriceAlert.State.TRIGGERED)
        form = self.form(instance=alert, signal="sell", note="تغییر")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().state, PriceAlert.State.TRIGGERED)

    def test_editing_paused_alert_keeps_it_paused(self):
        alert = make_alert(self.user, state=PriceAlert.State.PAUSED)
        form = self.form(instance=alert, threshold="999000")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().state, PriceAlert.State.PAUSED)
