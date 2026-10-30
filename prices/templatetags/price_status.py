from django import template

from prices import services

register = template.Library()


@register.inclusion_tag("prices/warning_banner.html")
def price_reading_warning():
    """The admin banner shown while price reading has been failing for over 5 minutes (FR-024)."""
    return {"stale": services.is_stale(), "last_ok": services.latest_ok_reading()}
