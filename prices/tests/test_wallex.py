import json
import socket
import urllib.error
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.test import SimpleTestCase

from prices import wallex
from prices.tests.helpers import http_error, patch_urlopen

NOW = datetime(2026, 10, 29, 20, 5, tzinfo=dt_timezone.utc)


def body_with(price="271165", timestamp="2026-10-29T20:02:29Z"):
    return json.dumps(
        {"success": True, "result": {"latestTrades": [{"price": price, "timestamp": timestamp}]}}
    ).encode()


class FetchLatestTradeTests(SimpleTestCase):
    def test_uses_newest_trade_and_rounds_price(self):
        with patch_urlopen("trades_ok.json"):
            price, traded_at = wallex.fetch_latest_trade(now=NOW)
        self.assertEqual(price, Decimal("271166"))  # 271165.5 rounded half up
        self.assertEqual(traded_at, datetime(2026, 10, 29, 20, 2, 29, tzinfo=dt_timezone.utc))

    def test_request_url_headers_and_timeout(self):
        with patch_urlopen("trades_ok.json") as urlopen:
            wallex.fetch_latest_trade(now=NOW)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.wallex.ir/v1/trades?symbol=USDTTMN")
        self.assertEqual(request.get_header("User-agent"), "prodemy-price-alerts/1.0")
        self.assertEqual(request.get_header("Accept"), "application/json")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 10)

    def assertFails(self, expected_error, **patch_kwargs):
        with patch_urlopen(**patch_kwargs):
            with self.assertRaises(wallex.WallexError) as ctx:
                wallex.fetch_latest_trade(now=NOW)
        self.assertEqual(str(ctx.exception), expected_error)

    def test_network_errors(self):
        self.assertFails("network: timed out", error=socket.timeout("timed out"))
        self.assertFails(
            "network: [Errno 61] Connection refused",
            error=urllib.error.URLError(ConnectionRefusedError(61, "Connection refused")),
        )

    def test_http_errors(self):
        for code in (422, 429, 500):
            with self.subTest(code=code):
                self.assertFails(f"http {code}", error=http_error(code))

    def test_bad_responses(self):
        for name in ("not_json.txt", "trades_success_false.json", "trades_empty.json"):
            with self.subTest(name=name):
                self.assertFails("bad response", body=name)

    def test_bad_data(self):
        self.assertFails("bad data", body="trades_bad_price.json")
        self.assertFails("bad data", body=body_with(price="-5"))
        self.assertFails("bad data", body=body_with(price="abc"))
        self.assertFails("bad data", body=body_with(timestamp="not a time"))
        future = (NOW + timedelta(minutes=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertFails("bad data", body=body_with(timestamp=future))

    def test_small_clock_difference_is_allowed(self):
        soon = (NOW + timedelta(minutes=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with patch_urlopen(body=body_with(timestamp=soon)):
            price, _ = wallex.fetch_latest_trade(now=NOW)
        self.assertEqual(price, Decimal("271165"))
