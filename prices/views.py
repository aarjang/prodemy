from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.templatetags.fa_format import jalali, toman
from prices import services


def price_status():
    """The latest price and its display state, shared by the home page and the JSON endpoint."""
    reading = services.latest_ok_reading()
    return {
        "reading": reading,
        "stale": services.is_stale(reading=reading),
        "no_recent_trades": reading is not None and not services.has_recent_trades(reading),
    }


@require_GET
def latest_json(request):
    status = price_status()
    reading = status["reading"]
    if reading is None:
        data = {"price": None, "stale": True}
    else:
        data = {
            "price": int(reading.price),
            "price_display": toman(reading.price),
            "fetched_at": reading.fetched_at.isoformat(),
            "traded_at": reading.traded_at.isoformat(),
            "fetched_at_display": jalali(reading.fetched_at),
            "traded_at_display": jalali(reading.traded_at),
            "stale": status["stale"],
            "no_recent_trades": status["no_recent_trades"],
        }
    response = JsonResponse(data, json_dumps_params={"ensure_ascii": False})
    response["Cache-Control"] = "no-store"
    return response
