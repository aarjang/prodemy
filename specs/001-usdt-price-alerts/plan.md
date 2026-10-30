# Implementation Plan: USDT Price Alerts

**Branch**: `001-usdt-price-alerts` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-usdt-price-alerts/spec.md`

## Summary

A Persian, right-to-left, dark-themed (black and blue) website that reads the last traded
USDT/Toman price from Wallex every 30 seconds, shows it publicly, and lets registered users
create buy/sell alerts on thresholds they set. When a price crosses a threshold, an in-site
notification is created (exactly once per crossing) and shown in a list with an unread
badge. Administrators manage users, alerts, notifications and price-reading health in the
Django admin.

Technical approach: a single Django 5.2 LTS project with server-rendered templates,
Bootstrap 5.3 RTL and vanilla JavaScript. A long-running management command
(`poll_prices`) reads Wallex's public recent-trades endpoint, stores each reading and
evaluates alerts in the same process. No task queue or cache server is needed. See
[research.md](research.md) for each decision.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS; `jdatetime` (Solar Hijri dates); `psycopg[binary]`
3 (production database driver). Frontend: Bootstrap 5.3.3 RTL and the Vazirmatn font, both
vendored as static files. Wallex is called with the Python standard library
(`urllib.request`), so no HTTP client package is added.

**Storage**: SQLite for local development; PostgreSQL 16 in production, through the Django
ORM only.

**Testing**: Django test framework (`django.test.TestCase`, test `Client`), with
`unittest.mock` replacing the Wallex call.

**Target Platform**: Linux server (web process + one `poll_prices` worker process);
modern desktop and mobile browsers.

**Project Type**: Server-rendered web application (single Django project).

**Performance Goals**: price read every 30 s; all active alerts evaluated within the same
cycle (target < 1 s for 10,000 active alerts; required ≤ 10 s for 20,000, SC-006); a notification visible to the user within
2 minutes of a crossing (SC-002).

**Constraints**: one Wallex request per 30 s (Wallex reports a limit of 600 per window, far
above this); no frontend build step; pages work without JavaScript; Persian RTL; dark theme
only; WCAG 2.1 AA contrast.

**Scale/Scope**: up to about 1,000 users and 20,000 active alerts (20 per user); about
86,000 price readings per 30 days; about 10 user-facing pages plus the admin.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Django-First Backend | Django only; server-rendered templates extending `base.html`; Django auth, admin, forms, messages, password-reset views reused; apps split by responsibility (`accounts`, `prices`, `alerts`, `core`); migrations committed. Added packages (`jdatetime`, `psycopg`) are pinned and justified in research.md. | PASS |
| II. Vanilla Frontend with Bootstrap | Bootstrap 5.3 RTL for all components; custom CSS loads after Bootstrap and only changes Bootstrap CSS variables for the black/blue palette; vanilla JS in static files; no inline scripts or styles; price and badge refresh is progressive enhancement (pages are complete when rendered). | PASS |
| III. Test-Backed Changes | Every model, form and view has `TestCase` tests; alert crossing and re-arm logic and the Wallex parser have unit tests with mocked responses. | PASS |
| IV. Secure by Default | CSRF, auto-escaping, password hashing untouched; secrets and DB settings from environment variables; production `DEBUG=False` and `check --deploy` gate; all input through Django forms; Bootstrap and font served locally. Users only see their own alerts and notifications (queries filtered by `request.user`). | PASS |
| V. Responsive, Accessible & Simple | Bootstrap grid, mobile-first, tested at 360 px; semantic HTML with labelled fields; palette contrast checked at ≥ 4.5:1; no queue or cache server — one polling process instead. | PASS |

No violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-usdt-price-alerts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── http-routes.md   # Pages and JSON endpoints the site exposes
│   └── wallex-source.md # What the site expects from Wallex
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
manage.py
requirements.txt
.env.example
config/                     # Django project: settings, root urls, wsgi/asgi
├── settings.py
├── urls.py
└── wsgi.py
core/                       # Shared pieces: home page, template filters, context processor
├── views.py
├── context_processors.py   # unread notification count for the navbar badge
└── templatetags/
    └── fa_format.py        # Persian digits, thousands separators, Jalali dates
accounts/                   # Custom email-based User, sign-up, sign-in/out, password reset
├── models.py
├── forms.py
├── views.py
├── urls.py
├── admin.py
└── tests/
prices/                     # Wallex client, PriceReading, poll_prices command, price JSON
├── models.py
├── wallex.py               # fetch + parse latest USDTTMN trade
├── services.py             # record_reading(), prune_old_readings()
├── views.py
├── urls.py
├── admin.py
├── management/commands/poll_prices.py
└── tests/
alerts/                     # PriceAlert, Notification, evaluation, user pages
├── models.py
├── forms.py
├── evaluation.py           # evaluate_alerts(reading)
├── views.py
├── urls.py
├── admin.py
└── tests/
templates/
├── base.html               # <html lang="fa" dir="rtl" data-bs-theme="dark">
├── core/  accounts/  prices/  alerts/  registration/
└── admin/base_site.html    # forces dark theme and blue accent in the admin
static/
├── css/app.css             # palette overrides on Bootstrap CSS variables
├── js/price-live.js        # refreshes price card from /prices/latest.json
├── js/notifications.js     # refreshes unread badge
├── fonts/vazirmatn/
└── vendor/bootstrap-5.3.3/ # bootstrap.rtl.min.css, bootstrap.bundle.min.js
```

**Structure Decision**: one Django project (`config`) with four apps at the repository
root. Tests live in each app's `tests/` package so `python manage.py test` finds them.
Shared templates and static files live in top-level `templates/` and `static/`.

## Complexity Tracking

No constitution violations to justify.

## Post-Design Constitution Re-check

Re-checked after writing [data-model.md](data-model.md), [contracts/](contracts/) and
[quickstart.md](quickstart.md): all five principles still PASS. The two JSON endpoints are
small read-only helpers for progressive enhancement, not an SPA API; the polling worker is a
Django management command, so no non-Django runtime is introduced.
