"""Shared factories for alert tests."""

import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from alerts.models import PriceAlert
from prices.models import PriceReading

User = get_user_model()
PASSWORD = "tether-alert-2026!"


def make_user(email="user@example.com", **kwargs):
    return User.objects.create_user(email, PASSWORD, **kwargs)


def make_alert(user, threshold="271000", direction=PriceAlert.Direction.ABOVE,
               signal=PriceAlert.Signal.BUY, **kwargs):
    return PriceAlert.objects.create(
        user=user, threshold=Decimal(threshold), direction=direction, signal=signal, **kwargs
    )


def make_ok_reading(price="271500", minutes_ago=0):
    now = timezone.now()
    return PriceReading.objects.create(
        fetched_at=now - timedelta(minutes=minutes_ago),
        status=PriceReading.Status.OK,
        price=Decimal(price),
        traded_at=now - timedelta(minutes=minutes_ago, seconds=30),
    )


def make_failed_reading():
    return PriceReading.objects.create(
        fetched_at=timezone.now(), status=PriceReading.Status.FAILED, error="http 500"
    )


def trades_body(price, timestamp=None):
    timestamp = timestamp or timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return json.dumps(
        {"success": True, "result": {"latestTrades": [{"price": str(price), "timestamp": timestamp}]}}
    ).encode()
