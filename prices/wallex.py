"""Client for Wallex's public recent-trades endpoint (contracts/wallex-source.md)."""

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from core.numbers import round_toman

TRADES_URL = "https://api.wallex.ir/v1/trades?symbol=USDTTMN"
USER_AGENT = "prodemy-price-alerts/1.0"
TIMEOUT_SECONDS = 10
MAX_CLOCK_SKEW = timedelta(minutes=5)


class WallexError(Exception):
    """A failed read. The message is the short reason stored on the PriceReading."""


def _parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError(value)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(value)
    return parsed


def fetch_latest_trade(now=None):
    """Return (price, traded_at) of the newest USDT/Toman trade on Wallex.

    The price is rounded to whole Toman. Raises WallexError on any failure.
    """
    now = now or timezone.now()
    request = urllib.request.Request(
        TRADES_URL, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise WallexError(f"http {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise WallexError(f"network: {exc.reason}") from exc
    except (socket.timeout, TimeoutError, OSError) as exc:
        raise WallexError(f"network: {exc}") from exc

    try:
        data = json.loads(body)
        trades = data["result"]["latestTrades"] if data.get("success") is True else None
    except (ValueError, TypeError, KeyError, AttributeError):
        trades = None
    if not isinstance(trades, list) or not trades:
        raise WallexError("bad response")

    try:
        newest = max(trades, key=lambda trade: _parse_timestamp(trade["timestamp"]))
        traded_at = _parse_timestamp(newest["timestamp"])
        price = round_toman(Decimal(str(newest["price"])))
    except (ValueError, TypeError, KeyError, InvalidOperation) as exc:
        raise WallexError("bad data") from exc
    if price <= 0 or traded_at > now + MAX_CLOCK_SKEW:
        raise WallexError("bad data")
    return price, traded_at
