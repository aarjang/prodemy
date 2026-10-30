"""Evaluate alerts after each successful price reading (FR-013, FR-014, FR-015)."""

import logging

from django.db import transaction
from django.utils import timezone

from alerts.models import Notification, PriceAlert
from prices.models import PriceReading

logger = logging.getLogger("alerts")


def evaluate_alerts(reading):
    """Fire and re-arm alerts against one successful reading. Returns (fired, rearmed).

    Runs in a single transaction. The unique (alert, price_reading) constraint plus
    ignore_conflicts makes a re-run on the same reading harmless (SC-003).
    """
    if reading.status != PriceReading.Status.OK:
        return 0, 0
    price = reading.price
    now = timezone.now()

    with transaction.atomic():
        active = PriceAlert.objects.filter(
            state__in=(PriceAlert.State.ARMED, PriceAlert.State.TRIGGERED),
            user__is_active=True,
        )
        firing = active.filter(state=PriceAlert.State.ARMED).filter(
            models_q_crossed(price)
        )
        fired_alerts = list(firing.values(
            "pk", "user_id", "signal", "direction", "threshold", "note"
        ))
        Notification.objects.bulk_create(
            [
                Notification(
                    user_id=alert["user_id"], alert_id=alert["pk"], price_reading=reading,
                    signal=alert["signal"], direction=alert["direction"],
                    threshold=alert["threshold"], note=alert["note"], price=price,
                )
                for alert in fired_alerts
            ],
            ignore_conflicts=True,
            batch_size=500,
        )
        fired = PriceAlert.objects.filter(pk__in=[a["pk"] for a in fired_alerts]).update(
            state=PriceAlert.State.TRIGGERED, last_triggered_at=now, updated_at=now
        )
        rearmed = (
            active.filter(state=PriceAlert.State.TRIGGERED)
            .filter(models_q_returned(price))
            .update(state=PriceAlert.State.ARMED, updated_at=now)
        )
    if fired or rearmed:
        logger.info("evaluated reading %s: fired=%s rearmed=%s", reading.pk, fired, rearmed)
    return fired, rearmed


def models_q_crossed(price):
    """Armed alerts whose condition is met: above → price >= X, below → price <= X."""
    from django.db.models import Q

    return Q(direction=PriceAlert.Direction.ABOVE, threshold__lte=price) | Q(
        direction=PriceAlert.Direction.BELOW, threshold__gte=price
    )


def models_q_returned(price):
    """Triggered alerts strictly back on the other side: above → price < X, below → price > X."""
    from django.db.models import Q

    return Q(direction=PriceAlert.Direction.ABOVE, threshold__gt=price) | Q(
        direction=PriceAlert.Direction.BELOW, threshold__lt=price
    )
