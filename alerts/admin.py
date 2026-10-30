from django.contrib import admin
from django.utils import timezone

from alerts.models import Notification, PriceAlert
from core.templatetags.fa_format import jalali, toman


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "threshold_toman", "direction", "signal", "state", "last_triggered_jalali")
    list_filter = ("state", "signal", "direction")
    search_fields = ("user__email",)
    actions = ("pause_alerts", "resume_alerts")

    @admin.display(description="قیمت آستانه (تومان)", ordering="threshold")
    def threshold_toman(self, obj):
        return toman(obj.threshold)

    @admin.display(description="آخرین فعال شدن", ordering="last_triggered_at")
    def last_triggered_jalali(self, obj):
        return jalali(obj.last_triggered_at) or "—"
    readonly_fields = ("last_triggered_at", "created_at", "updated_at")

    def has_add_permission(self, request):
        # Admins manage alerts but never create them for users (FR-022).
        return False

    @admin.action(description="توقف هشدارهای انتخاب‌شده")
    def pause_alerts(self, request, queryset):
        updated = queryset.exclude(state=PriceAlert.State.PAUSED).update(
            state=PriceAlert.State.PAUSED, updated_at=timezone.now()
        )
        self.message_user(request, f"{updated} هشدار متوقف شد.")

    @admin.action(description="ادامه هشدارهای انتخاب‌شده")
    def resume_alerts(self, request, queryset):
        # The per-user active limit applies here too (FR-018).
        resumed = skipped = 0
        for alert in queryset.filter(state=PriceAlert.State.PAUSED).select_related("user"):
            active = PriceAlert.objects.filter(
                user=alert.user, state__in=PriceAlert.ACTIVE_STATES
            ).count()
            if active >= PriceAlert.MAX_ACTIVE_PER_USER:
                skipped += 1
                continue
            alert.state = PriceAlert.State.ARMED
            alert.save(update_fields=["state", "updated_at"])
            resumed += 1
        message = f"{resumed} هشدار ادامه یافت."
        if skipped:
            message += f" {skipped} هشدار به دلیل سقف ۲۰ هشدار فعال کاربر رد شد."
        self.message_user(request, message)


class ReadFilter(admin.SimpleListFilter):
    title = "وضعیت خواندن"
    parameter_name = "read"

    def lookups(self, request, model_admin):
        return (("read", "خوانده‌شده"), ("unread", "خوانده‌نشده"))

    def queryset(self, request, queryset):
        if self.value() == "read":
            return queryset.filter(read_at__isnull=False)
        if self.value() == "unread":
            return queryset.filter(read_at__isnull=True)
        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "signal", "threshold_toman", "price_toman", "created_jalali", "read_jalali")
    list_filter = (ReadFilter, "created_at")

    @admin.display(description="قیمت آستانه (تومان)", ordering="threshold")
    def threshold_toman(self, obj):
        return toman(obj.threshold)

    @admin.display(description="قیمت (تومان)", ordering="price")
    def price_toman(self, obj):
        return toman(obj.price)

    @admin.display(description="زمان اعلان", ordering="created_at")
    def created_jalali(self, obj):
        return jalali(obj.created_at)

    @admin.display(description="زمان خوانده شدن", ordering="read_at")
    def read_jalali(self, obj):
        return jalali(obj.read_at) or "خوانده‌نشده"
    search_fields = ("user__email",)
    readonly_fields = [field.name for field in Notification._meta.fields]

    def has_add_permission(self, request):
        return False
