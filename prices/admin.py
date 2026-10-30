from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from core.templatetags.fa_format import jalali, toman
from prices.models import PriceReading
from prices.services import latest_ok_reading


@admin.register(PriceReading)
class PriceReadingAdmin(admin.ModelAdmin):
    change_list_template = "admin/prices/pricereading/change_list.html"
    list_display = ("status", "price_toman", "fetched_at_jalali", "traded_at_jalali", "error")
    list_filter = ("status",)
    readonly_fields = [field.name for field in PriceReading._meta.fields]

    @admin.display(description="قیمت (تومان)", ordering="price")
    def price_toman(self, obj):
        return toman(obj.price) or "—"

    @admin.display(description="زمان خواندن", ordering="fetched_at")
    def fetched_at_jalali(self, obj):
        return jalali(obj.fetched_at)

    @admin.display(description="زمان معامله", ordering="traded_at")
    def traded_at_jalali(self, obj):
        return jalali(obj.traded_at) or "—"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["last_ok"] = latest_ok_reading()
        extra_context["failures_24h"] = PriceReading.objects.filter(
            status=PriceReading.Status.FAILED,
            fetched_at__gte=timezone.now() - timedelta(hours=24),
        ).count()
        return super().changelist_view(request, extra_context=extra_context)
