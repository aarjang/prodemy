"""Read the Wallex price in a loop: `python manage.py poll_prices [--once]`."""

import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from prices import services
from prices.models import PriceReading

BACKOFF_SECONDS = 60
FAILURES_BEFORE_BACKOFF = 5
PRUNE_EVERY_SECONDS = 60 * 60


def next_delay(last_reading, consecutive_failures):
    """Seconds to wait before the next read (FR-005)."""
    base = settings.PRICE_POLL_SECONDS
    if last_reading.status == PriceReading.Status.FAILED and (
        last_reading.error == "http 429" or consecutive_failures >= FAILURES_BEFORE_BACKOFF
    ):
        return max(base, BACKOFF_SECONDS)
    return base


class Command(BaseCommand):
    help = "Read the last traded USDT/Toman price from Wallex every PRICE_POLL_SECONDS."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run a single cycle and exit.")

    def handle(self, *args, once=False, **options):
        consecutive_failures = 0
        last_prune = None
        try:
            while True:
                reading = self.run_cycle()
                consecutive_failures = (
                    consecutive_failures + 1 if reading.status == PriceReading.Status.FAILED else 0
                )
                if last_prune is None or time.monotonic() - last_prune >= PRUNE_EVERY_SECONDS:
                    pruned = services.prune_old_readings()
                    if pruned:
                        self.stdout.write(f"pruned {pruned} old readings")
                    last_prune = time.monotonic()
                if once:
                    return
                time.sleep(next_delay(reading, consecutive_failures))
        except KeyboardInterrupt:
            self.stdout.write("stopped")

    def run_cycle(self):
        reading = services.record_reading()
        stamp = timezone.localtime(reading.fetched_at).strftime("%Y-%m-%d %H:%M:%S")
        if reading.status == PriceReading.Status.OK:
            self.stdout.write(f"{stamp} ok price={reading.price} traded_at={reading.traded_at.isoformat()}")
        else:
            self.stdout.write(f"{stamp} failed {reading.error}")
        self.after_reading(reading)
        return reading

    def after_reading(self, reading):
        """Evaluate alerts against each successful reading (FR-013)."""
        from alerts.evaluation import evaluate_alerts

        fired, rearmed = evaluate_alerts(reading)
        if fired or rearmed:
            self.stdout.write(f"alerts: fired={fired} rearmed={rearmed}")
