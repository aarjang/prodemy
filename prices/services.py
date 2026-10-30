"""Recording price readings and answering questions about the latest price."""

from datetime import timedelta

from django.utils import timezone

from prices import wallex
from prices.models import PriceReading

STALE_AFTER = timedelta(minutes=5)
NO_RECENT_TRADES_AFTER = timedelta(minutes=60)
RETENTION = timedelta(days=30)


def record_reading():
    """Read the price from Wallex once and store the attempt, successful or not."""
    try:
        price, traded_at = wallex.fetch_latest_trade()
    except wallex.WallexError as exc:
        return PriceReading.objects.create(
            fetched_at=timezone.now(), status=PriceReading.Status.FAILED, error=str(exc)
        )
    return PriceReading.objects.create(
        fetched_at=timezone.now(), status=PriceReading.Status.OK, price=price, traded_at=traded_at
    )


def latest_ok_reading():
    return PriceReading.objects.filter(status=PriceReading.Status.OK).first()


def is_stale(now=None, reading=None):
    """True when no successful read has happened for more than 5 minutes (FR-003)."""
    now = now or timezone.now()
    reading = reading if reading is not None else latest_ok_reading()
    return reading is None or now - reading.fetched_at > STALE_AFTER


def has_recent_trades(reading, now=None):
    """False when the reading's trade is more than 60 minutes old (FR-003)."""
    if reading is None or reading.traded_at is None:
        return False
    now = now or timezone.now()
    return now - reading.traded_at <= NO_RECENT_TRADES_AFTER


def prune_old_readings(now=None):
    """Delete readings older than 30 days, keeping ones a notification references.

    Returns the number deleted.
    """
    now = now or timezone.now()
    deleted, _ = (
        PriceReading.objects.filter(fetched_at__lt=now - RETENTION)
        .filter(notifications__isnull=True)
        .delete()
    )
    return deleted
