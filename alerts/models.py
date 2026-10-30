from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class PriceAlert(models.Model):
    """A user's buy/sell signal on a threshold price X (FR-010, FR-011)."""

    class Direction(models.TextChoices):
        ABOVE = "above", "بالاتر از"
        BELOW = "below", "پایین‌تر از"

    class Signal(models.TextChoices):
        BUY = "buy", "خرید"
        SELL = "sell", "فروش"

    class State(models.TextChoices):
        ARMED = "armed", "فعال"
        TRIGGERED = "triggered", "فعال‌شده — منتظر بازگشت قیمت"
        PAUSED = "paused", "متوقف"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts",
        verbose_name="کاربر",
    )
    threshold = models.DecimalField(
        "قیمت آستانه (تومان)", max_digits=20, decimal_places=0,
        validators=[MinValueValidator(1)],
    )
    direction = models.CharField("جهت", max_length=10, choices=Direction.choices)
    signal = models.CharField("سیگنال", max_length=10, choices=Signal.choices)
    note = models.CharField("یادداشت", max_length=200, blank=True)
    state = models.CharField("وضعیت", max_length=10, choices=State.choices, default=State.ARMED)
    last_triggered_at = models.DateTimeField("آخرین فعال شدن", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ACTIVE_STATES = (State.ARMED, State.TRIGGERED)
    MAX_ACTIVE_PER_USER = 20

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "هشدار قیمت"
        verbose_name_plural = "هشدارهای قیمت"
        indexes = [models.Index(fields=["state", "direction", "threshold"])]

    def __str__(self):
        return f"{self.get_signal_display()} — {self.get_direction_display()} {self.threshold}"


class Notification(models.Model):
    """Created when an alert fires; keeps a copy of the alert's values (FR-016, FR-017)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications",
        verbose_name="کاربر",
    )
    alert = models.ForeignKey(
        PriceAlert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notifications", verbose_name="هشدار",
    )
    price_reading = models.ForeignKey(
        "prices.PriceReading", on_delete=models.PROTECT, related_name="notifications",
        verbose_name="خواندن قیمت",
    )
    signal = models.CharField("سیگنال", max_length=10, choices=PriceAlert.Signal.choices)
    direction = models.CharField("جهت", max_length=10, choices=PriceAlert.Direction.choices)
    threshold = models.DecimalField("قیمت آستانه (تومان)", max_digits=20, decimal_places=0)
    note = models.CharField("یادداشت", max_length=200, blank=True)
    price = models.DecimalField("قیمت لحظه فعال شدن (تومان)", max_digits=20, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField("زمان خوانده شدن", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        constraints = [
            models.UniqueConstraint(fields=["alert", "price_reading"], name="one_notification_per_crossing"),
        ]

    def __str__(self):
        return f"{self.get_signal_display()} {self.threshold} → {self.price}"
