from django.db import models
from django.db.models import Q


class PriceReading(models.Model):
    """One attempt to read the last traded USDT/Toman price from Wallex."""

    class Status(models.TextChoices):
        OK = "ok", "موفق"
        FAILED = "failed", "ناموفق"

    fetched_at = models.DateTimeField("زمان خواندن", db_index=True)
    status = models.CharField("وضعیت", max_length=10, choices=Status.choices)
    price = models.DecimalField("قیمت (تومان)", max_digits=20, decimal_places=0, null=True, blank=True)
    traded_at = models.DateTimeField("زمان معامله", null=True, blank=True)
    error = models.TextField("علت خطا", blank=True)

    class Meta:
        ordering = ["-fetched_at"]
        verbose_name = "خواندن قیمت"
        verbose_name_plural = "خواندن‌های قیمت"
        constraints = [
            models.CheckConstraint(
                name="price_reading_ok_or_failed",
                condition=(
                    Q(status="ok", price__gt=0, traded_at__isnull=False)
                    | Q(status="failed", price__isnull=True, traded_at__isnull=True)
                ),
            ),
        ]

    def __str__(self):
        if self.status == self.Status.OK:
            return f"{self.price} @ {self.fetched_at:%Y-%m-%d %H:%M:%S}"
        return f"failed ({self.error}) @ {self.fetched_at:%Y-%m-%d %H:%M:%S}"
