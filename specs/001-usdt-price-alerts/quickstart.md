# Quickstart & Validation: USDT Price Alerts

How to run the feature locally and prove it works end to end. Routes are in
[contracts/http-routes.md](contracts/http-routes.md); fields and states are in
[data-model.md](data-model.md).

## Prerequisites

- Python 3.12 (macOS: `brew install python@3.12`; the system Python 3.9 is too old for
  Django 5.2).
- Internet access to `api.wallex.ir` for the live-price scenarios.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DJANGO_SECRET_KEY; DEBUG=True for local work
python manage.py migrate
python manage.py createsuperuser
```

## Run

Two terminals:

```bash
python manage.py runserver
```

```bash
python manage.py poll_prices
```

`python manage.py poll_prices --once` does a single read and evaluation, then exits.

## Automated checks (all must pass — constitution quality gates)

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
DEBUG=False python manage.py check --deploy
```

## Manual validation scenarios

| # | Story | Steps | Expected |
|---|-------|-------|----------|
| 1 | US1 | Start the poller, open `/` | Price in Persian digits with "تومان", read time and last-trade time in Jalali; matches Wallex's USDT/TMN last trade |
| 2 | US1 | Leave `/` open for 1 minute | Price card updates without reload (read time changes) |
| 3 | US1 | Stop the poller, wait 6 minutes, reload `/` | Last price shown with a "قدیمی" (stale) badge |
| 4 | US2 | Sign up with a new email, sign out, sign in | Lands on `/alerts/`; second sign-up with the same email shows an error |
| 5 | US2 | Request a password reset | Reset email printed in the runserver terminal; link sets a new password |
| 6 | US3 | Create "above, buy" alert with X just below the current price; run `poll_prices --once` | One notification appears; navbar badge shows ۱; alert state = triggered |
| 7 | US3 | Run `poll_prices --once` again | No second notification |
| 8 | US3 | Create an alert with X = `-5`, `0`, `abc`; then a 21st active alert | Each is rejected with a Persian error |
| 9 | US3 | Mark notification read | Badge disappears; history keeps the entry |
| 10 | US4 | Open `/admin/` as superuser; deactivate the test user | User cannot sign in; their alerts no longer fire |
| 11 | US4 | Open `/admin/` as a normal user | Access refused |
| 12 | UI | Browser width 360 px on `/`, `/alerts/`, `/notifications/` and `/admin/` | Dark black/blue theme, right-to-left, no horizontal scroll |
| 13 | UI | Disable JavaScript, repeat scenarios 1 and 6 | Pages still work by reloading |

To force a crossing without waiting for the market, scenario 6 uses a threshold relative to
the current price; the automated tests cover crossings with mocked prices.

## Validation results (2026-10-30)

Automated gates all pass: `manage.py test` (120 tests), `check`,
`makemigrations --check --dry-run`, and `check --deploy` with production settings.

| # | Result | How it was checked |
|---|--------|--------------------|
| 1 | ✅ | Live in the browser against real Wallex data; price, read time and trade time shown in Persian/Jalali and matched the poller's log. |
| 2 | ✅ | Live: with the page open and the poller running, the read time advanced (۱۲:۰۷ → ۱۲:۰۸) without a reload. |
| 3 | ✅ | Automated tests (`prices` services + home view: stale badge after 5 min, "no recent trades" after 60 min). Manual wait skipped because the local poller keeps the price fresh. |
| 4 | ✅ | Live: signed up `demo@example.com`, signed out and back in; duplicate-email refusal covered by tests. |
| 5 | ✅ | Live: reset requested in the browser; the Persian email with a working link appeared in the dev server log. The link-to-new-password flow is covered by tests. |
| 6 | ✅ | Live: created "above ۲۷۱٬۰۰۰ → buy" with the real price ≈271,500; one poll cycle fired exactly one notification; badge showed ۱; alert became triggered. |
| 7 | ✅ | Live: a second poll cycle on the same conditions fired nothing. |
| 8 | ✅ | Automated form/view tests (zero, negative, non-numeric, fractional thresholds; 21st active alert refused, paused alerts not counted). |
| 9 | ✅ | Live: "خوانده شد" cleared the badge; the entry stayed in the history. |
| 10 | ✅ | Admin action tests (deactivate/reactivate) plus evaluation tests proving inactive users' alerts are skipped; inactive sign-in refusal tested. |
| 11 | ✅ | Live: a signed-in non-staff user hitting /admin/ was sent to the admin login with an authorization message; also covered by a test. |
| 12 | ✅ | Live at 375 px: home, alerts (table stacks into cards), notifications, login and admin — dark, RTL, no horizontal scroll. |
| 13 | ✅ | By design plus automated tests: every page is fully server-rendered (prices, badge and forms present without JavaScript); scripts only refresh values. Not separately exercised in a JS-disabled browser. |

Environment note: the venv was created with `uv` (Python 3.12.13); use
`uv pip install -r requirements.txt` since the venv has no pip. A local dev superuser
`admin@example.com` exists; its password is in `.env` (`SEED_ADMIN_PASSWORD`).
