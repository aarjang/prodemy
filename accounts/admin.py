from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.forms import SignUpForm
from accounts.models import User
from core.templatetags.fa_format import jalali


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Email-based user admin (the model has no username)."""

    add_form = SignUpForm
    ordering = ("email",)
    list_display = ("email", "is_active", "is_staff", "joined_jalali")

    @admin.display(description="تاریخ عضویت", ordering="date_joined")
    def joined_jalali(self, obj):
        return jalali(obj.date_joined)
    list_filter = ("is_active", "is_staff")
    search_fields = ("email",)
    actions = ("deactivate_users", "reactivate_users")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("دسترسی", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌ها", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)

    @admin.action(description="غیرفعال کردن کاربران انتخاب‌شده")
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} کاربر غیرفعال شد.")

    @admin.action(description="فعال کردن کاربران انتخاب‌شده")
    def reactivate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} کاربر فعال شد.")
