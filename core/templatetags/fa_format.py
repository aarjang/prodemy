"""Template filters for Persian display: digits, Toman amounts and Jalali dates."""

import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_MONTHS = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)


@register.filter
def fa_digits(value):
    """Replace Western digits with Persian digits."""
    if value is None:
        return ""
    return str(value).translate(_FA_DIGITS)


@register.filter
def toman(value):
    """Format a whole Toman amount with the Persian thousands separator, e.g. ۲۷۱٬۱۶۵."""
    if value is None or value == "":
        return ""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""
    return fa_digits(f"{number:,}".replace(",", "٬"))


@register.filter
def jalali(value):
    """Format an aware datetime as Tehran time in the Jalali calendar, e.g. ۸ آبان ۱۴۰۵، ۱۰:۵۷."""
    if value is None:
        return ""
    local = timezone.localtime(value)
    j = jdatetime.datetime.fromgregorian(datetime=local)
    return fa_digits(f"{j.day} {_MONTHS[j.month - 1]} {j.year}، {j.hour:02d}:{j.minute:02d}")
