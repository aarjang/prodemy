# Contract: Wallex Price Source

What `prices/wallex.py` expects from Wallex. Checked against the live API on 2026-10-30;
Wallex's developer docs site returned no readable content, so this is based on observed
responses.

## Request

```text
GET https://api.wallex.ir/v1/trades?symbol=USDTTMN
Accept: application/json
User-Agent: prodemy-price-alerts/1.0
Timeout: 10 seconds
```

No API key. One request per poll cycle (default every 30 s).

## Successful response (HTTP 200)

```json
{
  "success": true,
  "message": "عملیات موفقیت‌آمیز بود.",
  "result": {
    "latestTrades": [
      {
        "symbol": "USDTTMN",
        "quantity": "9.6600000000000000",
        "price": "271165.0000000000000000",
        "sum": "2619453.9000000000000000",
        "isBuyOrder": true,
        "timestamp": "2026-10-29T20:02:29Z"
      }
    ]
  }
}
```

The client uses the trade with the newest `timestamp` (not just the first item).

## Parsed result

| Output | Source | Rule |
|--------|--------|------|
| `price` | newest trade `price` | `Decimal`, rounded to the nearest whole Toman (halves up, FR-006), must be > 0 |
| `traded_at` | newest trade `timestamp` | ISO 8601 UTC, must not be more than 5 minutes in the future (tolerance for clock differences; later = "future" under FR-004) |

## Failures → `PriceReading(status="failed")`, no alert evaluation

| Condition | Recorded `error` |
|-----------|------------------|
| Timeout or connection error | `network: <reason>` |
| HTTP status ≠ 200 (e.g. 422 unknown symbol, 429, 5xx) | `http <status>` |
| Body is not JSON, `success` is not true, or `latestTrades` missing/empty | `bad response` |
| Price not numeric, ≤ 0, or timestamp invalid | `bad data` |

On HTTP 429 or 5 consecutive failures the poller waits 60 s before the next attempt.

## Test fixtures

Tests store sample bodies in `prices/tests/fixtures/` (`trades_ok.json`,
`trades_empty.json`, `trades_bad_price.json`) and mock `urllib.request.urlopen`; tests never
call Wallex.
