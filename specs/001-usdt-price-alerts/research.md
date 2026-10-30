# Research: USDT Price Alerts

All Technical Context items are resolved; no NEEDS CLARIFICATION remains.

## R1. Which Wallex endpoint to read

- **Decision**: `GET https://api.wallex.ir/v1/trades?symbol=USDTTMN`, using the newest entry of
  `result.latestTrades` (`price`, `timestamp`).
- **Rationale**: checked live on 2026-10-30. It is public (no API key), small (about 9 KB for
  50 trades), and is the only endpoint seen that gives the last trade's time. The spec's
  "price" is the last traded price (Clarifications), which this is directly.
- **Alternatives considered**: `GET /v1/markets` has `stats.lastPrice` for USDTTMN but is about
  440 KB for all 373 markets and has no trade time — wasteful every 30 s. Websocket streaming
  could not be confirmed from the docs (the docs site renders client-side and returned no
  content), so it is not relied on.
- **Observed facts**: response `{"success": true, "message": "...", "result": {"latestTrades":
  [{"symbol", "quantity", "price", "sum", "isBuyOrder", "timestamp"}]}}`; prices are decimal
  strings in Toman (market `quotePrecision` 0); unknown symbol → HTTP 422. Headers include
  `x-ratelimit-limit: 600` and `cache-control: max-age=1`.
- **Note**: the last trade can be hours old during quiet periods (one check showed a trade
  about 11 hours old). The site therefore shows both "read at" and "last trade at".

## R2. Polling interval and rate limits

- **Decision**: poll every 30 s (setting `PRICE_POLL_SECONDS`, default 30). On failure, retry
  at the next cycle; after 5 consecutive failures, back off to 60 s until a success.
- **Rationale**: meets FR-001 (≤ 1 min) with margin, and 2 requests/min is far below the
  reported 600 limit. Backoff avoids hammering Wallex when it is down.
- **Alternatives considered**: 5–10 s polling gives little benefit for alerts and raises
  rate-limit risk.

## R3. How to run the periodic job

- **Decision**: a Django management command `poll_prices` that loops forever, run as its own
  process (systemd service in production, a second terminal in development). It has a
  `--once` flag for tests and cron-style use.
- **Rationale**: no Celery, Redis or cron dependency (Constitution I and V). One process means
  no concurrent evaluation of the same reading, which keeps "exactly once" simple.
- **Alternatives considered**: Celery beat (needs a broker — too heavy), cron every minute
  (cannot do 30 s and adds start-up cost each run), a thread inside the web process (runs once
  per web worker → duplicate reads).

## R4. Alert evaluation and exactly-once delivery

- **Decision**: after each successful reading, `evaluate_alerts(reading)` runs in one
  database transaction. Each alert has a state: `armed`, `triggered` or `paused`. An `armed`
  alert fires when `price >= X` (above) or `price <= X` (below): a Notification is created and
  the alert becomes `triggered`. A `triggered` alert returns to `armed` when the price is
  strictly back on the other side (`price < X` for above, `price > X` for below). A unique
  constraint on (alert, price_reading) blocks duplicate notifications even if a cycle is
  re-run.
- **Rationale**: matches FR-011–FR-015 and SC-003; the state field makes re-arming visible to
  users and admins.
- **Alternatives considered**: comparing with the previous reading only (fails when the poller
  restarts or a reading is missed); a cooldown timer (still floods when price hovers).
- **New alerts** start `armed`, so an alert already true at creation fires on the next cycle
  (spec edge case).
- **Only observed prices count**: crossings that happen while reading is down are not
  notified. Evaluation loads alerts once at the start of the cycle inside the transaction, so a
  user's edit or delete during a cycle applies from the next cycle.

## R5. Money and number handling

- **Decision**: store prices as `DecimalField(max_digits=20, decimal_places=0)` (whole Toman);
  parse Wallex strings with `Decimal`, rejecting non-numeric, zero or negative values. Forms
  accept Persian (۰–۹), Arabic-Indic and Western digits and thousands separators, normalized
  before validation.
- **Rationale**: floats are wrong for money; Wallex Toman precision is 0.
- **Display**: Persian digits with "٬" thousands separator via a `fa_format` template filter
  (e.g. ۲۷۱٬۱۶۵ تومان).

## R6. Dates, time zone and language

- **Decision**: `LANGUAGE_CODE = "fa"`, `TIME_ZONE = "Asia/Tehran"`, `USE_TZ = True`; Jalali
  display through `jdatetime` in a template filter (`jalali`). All UI text is written directly
  in Persian in templates; Django's own Persian translations cover auth and admin messages.
- **Rationale**: `jdatetime` is a small, pure-Python, widely used package — writing a Solar
  Hijri converter by hand is error-prone (Constitution I: justified dependency).
- **Alternatives considered**: `django-jalali` (adds model fields we don't need); full i18n
  with `.po` files (only one language is required).

## R7. Dark theme, palette and RTL

- **Decision**: Bootstrap 5.3.3 RTL build (`bootstrap.rtl.min.css`) with
  `<html lang="fa" dir="rtl" data-bs-theme="dark">`. `static/css/app.css` overrides Bootstrap's
  dark-mode CSS variables: body background `#0a0a0a`, surfaces `#121417`/`#1a1d21`, primary
  blue `#3b82f6` (buttons `#2563eb`), links `#60a5fa`, text `#e5e7eb`, muted text `#9ca3af`.
  Computed contrast (WCAG formula): `#e5e7eb` on `#0a0a0a` 16.0:1; `#3b82f6` on `#0a0a0a`
  5.4:1; `#60a5fa` links on `#1a1d21` cards 6.7:1; white on `#2563eb` buttons 5.2:1; muted
  `#9ca3af` on `#1a1d21` 6.7:1 — all ≥ 4.5:1. Font: Vazirmatn (SIL OFL), vendored under `static/fonts/`.
- **Admin**: override `templates/admin/base_site.html` to set `data-theme="dark"` (Django's
  admin has a built-in dark theme) and blue `--primary` / `--secondary` variables; with
  `LANGUAGE_CODE="fa"` the admin renders RTL automatically. The admin theme toggle is hidden.
- **Rationale**: FR-026, FR-028, FR-029; Bootstrap's built-in color modes keep custom CSS to
  variables only (Constitution II).
- **Alternatives considered**: CDN delivery (blocked or slow for some Iranian networks — local
  files are more reliable and satisfy Constitution IV); Bootstrap Sass rebuild (needs a build
  step).

## R8. Live updates in the browser

- **Decision**: pages render the price and unread count on the server. Two small vanilla JS
  files poll `GET /prices/latest.json` (every 30 s) and `GET /notifications/unread-count.json`
  (every 60 s, signed-in users) with `fetch`, and update the DOM. Polling pauses while the tab
  is hidden (`document.visibilityState`).
- **Rationale**: progressive enhancement (works without JS by reloading); far simpler than
  WebSockets/Channels.
- **Alternatives considered**: Django Channels (needs ASGI server and Redis), `<meta refresh>`
  (reloads whole page and loses form input).

## R9. Accounts

- **Decision**: custom `accounts.User` (subclass of `AbstractUser`) with `email` unique and
  used as `USERNAME_FIELD`, created at project start before the first migration. Django's
  built-in `LoginView`, `LogoutView` and `PasswordReset*` views with Persian templates; a
  simple sign-up view using a `UserCreationForm` subclass. Admin role = `is_staff`. Deactivated
  users have `is_active=False`, which blocks sign-in and is excluded from alert evaluation.
- **Email**: console backend in development; SMTP from environment variables in production
  (only used for password reset).
- **Rationale**: Django recommends a custom user model from day one; email login is required
  by the spec.

## R10. Retention and housekeeping

- **Decision**: `poll_prices` deletes readings older than 30 days once per hour, except
  readings referenced by a notification (kept so history stays accurate).
- **Rationale**: spec assumption (≥ 30 days); keeps the table at about 86,000 rows.

## R11. Production database and deployment basics

- **Decision**: PostgreSQL 16 with `psycopg` 3, configured from `DB_*` environment variables;
  SQLite when `DB_ENGINE` is unset. Gunicorn is not required by this plan (deployment details
  belong to a later feature), but `check --deploy` must pass.
- **Rationale**: the web process and the poller write at the same time; PostgreSQL handles
  this better than SQLite.
