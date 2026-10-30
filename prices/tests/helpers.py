"""Helpers for faking Wallex responses in tests. Tests never call Wallex."""

import io
import urllib.error
from pathlib import Path
from unittest import mock

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name):
    return (FIXTURES / name).read_bytes()


def fake_response(body):
    """A context-manager response like the one urllib.request.urlopen returns."""
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = body
    response.status = 200
    return response


def patch_urlopen(body=None, error=None):
    """Patch urlopen in prices.wallex to return `body` (bytes or fixture name) or raise `error`."""
    if isinstance(body, str):
        body = fixture_bytes(body)
    target = "prices.wallex.urllib.request.urlopen"
    if error is not None:
        return mock.patch(target, side_effect=error)
    return mock.patch(target, return_value=fake_response(body))


def http_error(code):
    return urllib.error.HTTPError(
        "https://api.wallex.ir/v1/trades?symbol=USDTTMN", code, "error", hdrs=None, fp=io.BytesIO(b"")
    )
