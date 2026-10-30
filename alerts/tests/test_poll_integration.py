from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from alerts.models import Notification
from alerts.tests.helpers import make_alert, make_user, trades_body
from prices.tests.helpers import patch_urlopen


class PollEvaluatesAlertsTests(TestCase):
    def test_two_polls_past_threshold_create_exactly_one_notification(self):
        user = make_user()
        make_alert(user, threshold="271000")
        for _ in range(2):
            with patch_urlopen(body=trades_body("271500")):
                call_command("poll_prices", "--once", stdout=StringIO())
        self.assertEqual(Notification.objects.filter(user=user).count(), 1)
