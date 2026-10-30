---

description: "Task list for USDT Price Alerts"
---

# Tasks: USDT Price Alerts

**Input**: Design documents from `/specs/001-usdt-price-alerts/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included. The constitution (Principle III) requires tests for every model, form
and view, and a bug fix needs a reproducing test. Within each story, write the tests first
and see them fail before implementing.

**Organization**: Tasks are grouped by user story so each story can be built and checked on
its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: The user story the task belongs to (US1–US4)
- Paths are relative to the repository root (`/Users/arjang/project/prodemy`), following the
  structure in [plan.md](plan.md)

## Conventions for every task

- All user-facing text is Persian. Templates extend `templates/base.html`. No inline `style`
  attributes or inline `<script>` blocks; JavaScript lives in `static/js/`.
- Prices are `Decimal` whole Toman (`DecimalField(max_digits=20, decimal_places=0)`); times
  are timezone-aware and shown in Asia/Tehran with the Jalali calendar.
- Users only see their own alerts and notifications: always filter by `request.user`; another
  user's object id returns 404.
- Every successful POST redirects (Post/Redirect/Get) and adds a Persian Django message.
- Tests never call Wallex; they mock `urllib.request.urlopen`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Django project, dependencies and static assets.

- [X] T001 Create a Python 3.12 virtual environment `.venv/` and `requirements.txt` with exact pins (`==`) for the latest available patch releases of `Django` 5.2 LTS, `jdatetime` and `psycopg[binary]` 3; install them
- [X] T002 Create the Django project with `django-admin startproject config .` (giving `manage.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py`) and the apps `core`, `accounts`, `prices`, `alerts` with `python manage.py startapp`; replace each app's `tests.py` with a `tests/__init__.py` package
- [X] T003 [P] Create `.gitignore` (`.venv/`, `__pycache__/`, `*.sqlite3`, `.env`, `staticfiles/`, `media/`) and `.env.example` listing `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, `PRICE_POLL_SECONDS` with safe example values
- [X] T004 [P] Vendor Bootstrap 5.3.3 into `static/vendor/bootstrap-5.3.3/` (`css/bootstrap.rtl.min.css`, `js/bootstrap.bundle.min.js`, and the matching `.map` files) from the official distribution, and record the source URL and version in `static/vendor/README.md`
- [X] T005 [P] Vendor the Vazirmatn font (SIL OFL) into `static/fonts/vazirmatn/` (WOFF2 weights 400, 500 and 700 plus `OFL.txt`) and record the source in `static/vendor/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings, the custom user model, the base layout and shared formatting — needed
by every story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The custom user
model (T007) MUST exist before the first `migrate`.

- [X] T006 Configure `config/settings.py`: read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (default `False`) and `DJANGO_ALLOWED_HOSTS` from the environment (load `.env` with a small stdlib parser, no extra package); `INSTALLED_APPS` adds `core`, `accounts`, `prices`, `alerts`; `LANGUAGE_CODE = "fa"`, `TIME_ZONE = "Asia/Tehran"`, `USE_TZ = True`; `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`; `STATICFILES_DIRS = [BASE_DIR / "static"]`, `STATIC_ROOT = BASE_DIR / "staticfiles"`; `AUTH_USER_MODEL = "accounts.User"`; `LOGIN_URL = "login"`, `LOGIN_REDIRECT_URL = "core:home"` (US3 changes it to `alerts:list` in T051), `LOGOUT_REDIRECT_URL = "core:home"`; SQLite when `DB_ENGINE` is unset, otherwise PostgreSQL from `DB_*`; console email backend when `DEBUG`, SMTP from `EMAIL_*` otherwise; `PRICE_POLL_SECONDS = int(env or 30)`; when not `DEBUG`: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS = 31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_PROXY_SSL_HEADER`
- [X] T007 Create the custom user model in `accounts/models.py`: `User(AbstractUser)` with `username = None`, `email = models.EmailField(unique=True)`, `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`, and a `UserManager` with `create_user` / `create_superuser` that lowercases the email ("required, unique (case-insensitive: stored lowercased)")
- [X] T008 [P] Write model tests in `accounts/tests/test_models.py`: email stored lowercased; duplicate email in different case raises `IntegrityError`; `create_superuser` sets `is_staff` and `is_superuser`; user with no email is rejected
- [X] T009 Create the initial migrations with `python manage.py makemigrations accounts` and run `python manage.py migrate` (accounts first, before any other app migration)
- [X] T010 [P] Write template filters in `core/templatetags/fa_format.py`: `fa_digits` (Western → Persian digits), `toman` (thousands separator `٬` + Persian digits, e.g. `۲۷۱٬۱۶۵`), `jalali` (aware datetime → Tehran Jalali string such as `۸ آبان ۱۴۰۵، ۱۰:۵۷` using `jdatetime`); `None` input returns an empty string
- [X] T011 [P] Write tests for the filters in `core/tests/test_fa_format.py`: `toman(Decimal("271165"))` → `۲۷۱٬۱۶۵`; `jalali` of `2026-10-30T07:27:00Z` → `۸ آبان ۱۴۰۵، ۱۰:۵۷`; `None` → `""`
- [X] T012 [P] Write `core/numbers.py` with `parse_toman(text) -> Decimal` that accepts Persian (۰–۹), Arabic-Indic (٠–٩) and Western digits, removes the separators `,` `٬` `،` and spaces, and raises `ValueError` for empty, non-numeric or fractional input; and `round_toman(value: Decimal) -> Decimal` rounding to the nearest whole Toman with `ROUND_HALF_UP` (FR-006)
- [X] T013 [P] Write tests in `core/tests/test_numbers.py` for `parse_toman` (`"۲۷۱٬۱۶۵"`, `"271,165"`, `"٢٧١١٦٥"` → `271165`; `"abc"`, `""`, `"12.5"` → `ValueError`) and `round_toman` (`271165.5` → `271166`, `271165.4` → `271165`)
- [X] T014 [P] Create the palette in `static/css/app.css`: `@font-face` for Vazirmatn; on `[data-bs-theme=dark]` set `--bs-body-bg: #0a0a0a`, `--bs-body-color: #e5e7eb`, `--bs-secondary-color: #9ca3af`, `--bs-tertiary-bg: #121417`, `--bs-secondary-bg: #1a1d21`, `--bs-primary: #3b82f6`, `--bs-primary-rgb`, `--bs-link-color: #60a5fa`, `--bs-link-hover-color: #93c5fd`, `--bs-border-color: #2a2f36`, and `.btn-primary` background `#2563eb` with white text (research.md R7; every pair ≥ 4.5:1); use `font-family: Vazirmatn, system-ui, sans-serif`
- [X] T015 Create `templates/base.html`: `<html lang="fa" dir="rtl" data-bs-theme="dark">`, viewport meta, `bootstrap.rtl.min.css` then `css/app.css`, a Bootstrap navbar that works without JavaScript — use `navbar-expand` (always expanded, no `navbar-toggler` / `collapse`) with the nav links in a `flex-wrap` list so they wrap onto a second line at 360 px (constitution II: core content works with JavaScript off) — containing the brand, a link to home, and blocks for signed-in links and the notification badge filled by later stories, a Django messages area as Bootstrap alerts, `{% block content %}`, `bootstrap.bundle.min.js` and `{% block scripts %}` at the end of `<body>`; landmarks `<header>`, `<main>`, `<footer>`
- [X] T016 Create `config/urls.py` with `admin/`, `accounts/` (`django.contrib.auth.urls` plus `accounts.urls`), `""` → `core.urls`, `prices/` → `prices.urls`, `""` → `alerts.urls`; create empty `urls.py` with `app_name` in `core`, `accounts`, `prices` and `alerts`
- [X] T017 Run `python manage.py check` and `python manage.py test` and confirm both pass before starting a story

**Checkpoint**: Foundation ready — user story work can begin.

---

## Phase 3: User Story 1 - See the current USDT price (Priority: P1) 🎯 MVP

**Goal**: Read the last traded USDT/Toman price from Wallex every 30 s, store every attempt,
and show the price publicly with read time, trade time, stale and "no recent trades" states.

**Independent Test**: Run `python manage.py poll_prices --once`, open `/`, and compare the
price with Wallex's last USDT/TMN trade; stop the poller for 6 minutes and the page shows the
stale badge (quickstart scenarios 1–3).

### Tests for User Story 1 ⚠️ (write first, see them fail)

- [X] T018 [P] [US1] Create Wallex fixtures in `prices/tests/fixtures/`: `trades_ok.json` (the sample body from contracts/wallex-source.md with at least 3 trades, newest not first), `trades_empty.json` (`latestTrades: []`), `trades_bad_price.json` (price `"0"`), `trades_success_false.json` (`"success": false`), `not_json.txt`
- [X] T019 [P] [US1] Write client tests in `prices/tests/test_wallex.py` (mock `urllib.request.urlopen`): picks the trade with the newest `timestamp`; price parsed with `Decimal` and rounded with `round_toman`; failures map to the error strings `network: <reason>`, `http <status>` (422, 429, 500), `bad response` (not JSON, `success` not true, empty list), `bad data` (price ≤ 0 or not numeric, timestamp invalid or more than 5 minutes in the future); request uses the URL `https://api.wallex.ir/v1/trades?symbol=USDTTMN`, header `User-Agent: prodemy-price-alerts/1.0` and a 10-second timeout
- [X] T020 [P] [US1] Write model and service tests in `prices/tests/test_services.py`: `record_reading` stores an `ok` reading with `price` and `traded_at`, or a `failed` reading with `error` and null `price`; `latest_ok_reading()` ignores failed rows; `is_stale()` true when the newest ok `fetched_at` is more than 5 minutes ago or no ok reading exists; `has_recent_trades()` false when `traded_at` is more than 60 minutes ago; `prune_old_readings()` deletes rows older than 30 days
- [X] T021 [P] [US1] Write command tests in `prices/tests/test_poll_prices.py`: `call_command("poll_prices", "--once")` records exactly one reading; the delay helper returns `PRICE_POLL_SECONDS` normally and at least 60 seconds after an `http 429` failure or after 5 failures in a row, and returns to normal after a success (FR-005)
- [X] T022 [P] [US1] Write view tests in `prices/tests/test_views.py` and `core/tests/test_home.py`: `GET /prices/latest.json` returns the keys `price`, `price_display`, `fetched_at`, `traded_at`, `fetched_at_display`, `stale`, `no_recent_trades` and header `Cache-Control: no-store`; with no ok reading returns HTTP 200 `{"price": null, "stale": true}`; `GET /` shows the Persian price, the read time and trade time, the stale badge, the "no recent trades" note, and the empty-state message in the matching situations

### Implementation for User Story 1

- [X] T023 [US1] Create `PriceReading` in `prices/models.py` with fields `fetched_at` (datetime, indexed), `status` (choices `ok` / `failed`), `price` (`DecimalField(max_digits=20, decimal_places=0)`, nullable — "required and > 0 when `ok`; null when `failed`"), `traded_at` (datetime, nullable — "required when `ok`"), `error` (text, blank — "short failure reason when `failed`"); `Meta.ordering = ["-fetched_at"]`; a `CheckConstraint` enforcing the ok/failed field rules; run `makemigrations prices`
- [X] T024 [US1] Implement `prices/wallex.py`: `fetch_latest_trade() -> (price: Decimal, traded_at: datetime)` using `urllib.request` per contracts/wallex-source.md, raising `WallexError(error_string)` for every failure listed there
- [X] T025 [US1] Implement `prices/services.py`: `record_reading()` (calls the client, saves an ok or failed `PriceReading`, returns it), `latest_ok_reading()`, `is_stale(now=None)` (5 minutes), `has_recent_trades(reading, now=None)` (60 minutes), `prune_old_readings(now=None)` (older than 30 days; skip rows referenced by a notification once US3 adds that relation — guard with `hasattr`/related query so US1 stands alone)
- [X] T026 [US1] Implement the management command `prices/management/commands/poll_prices.py`: loop forever calling `record_reading()`; sleep per a `next_delay(last_reading, consecutive_failures)` helper (`PRICE_POLL_SECONDS`, ≥ 60 s after `http 429` or 5 consecutive failures); call `prune_old_readings()` once per hour; `--once` flag does a single cycle; log each cycle to stdout; exit cleanly on Ctrl+C. Leave a clearly named `after_reading(reading)` step that US3 fills with alert evaluation
- [X] T027 [P] [US1] Implement `prices/views.py` `latest_json` (route `/prices/latest.json`, name `prices:latest_json`) returning the JSON from contracts/http-routes.md, using the `toman` and `jalali` filters for display fields; add it to `prices/urls.py`
- [X] T028 [US1] Implement the home view in `core/views.py` (`core:home`, route `/`) and `templates/core/home.html`: a Bootstrap card with the price (`toman` + "تومان"), "زمان خواندن" and "زمان آخرین معامله" in Jalali, a stale badge ("قدیمی") when `is_stale`, a "معامله اخیری ثبت نشده" note when there are no recent trades, an empty state "قیمت هنوز در دسترس نیست" when there is no reading; mark elements with `data-*` attributes the script updates; add the route to `core/urls.py`
- [X] T029 [P] [US1] Write `static/js/price-live.js` (loaded only on the home page via `{% block scripts %}`): every 30 s `fetch("/prices/latest.json")` and update the price card elements and badges; skip while `document.visibilityState === "hidden"`; do nothing on fetch errors (the server-rendered values stay)

**Checkpoint**: The public price page works on its own (quickstart scenarios 1–3).

---

## Phase 4: User Story 2 - Sign up and sign in (Priority: P1)

**Goal**: Visitors register with email and password, sign in and out, and reset a forgotten
password by email.

**Independent Test**: Sign up, sign out, sign back in and land on the home page (the alerts
page once US3 is built); a duplicate email is refused; a reset email appears in the console
(quickstart scenarios 4–5).

### Tests for User Story 2 ⚠️

- [X] T030 [P] [US2] Write form tests in `accounts/tests/test_forms.py`: `SignUpForm` accepts a valid email and matching passwords, lowercases the email, rejects an existing email in any letter case with a Persian error, and applies Django's password validators
- [X] T031 [P] [US2] Write view tests in `accounts/tests/test_views.py`: `POST /accounts/signup/` creates the user, signs them in and redirects to `core:home`; signed-in users opening sign-up are redirected; wrong password at `/accounts/login/` shows one generic error; an inactive user cannot sign in; `POST /accounts/logout/` signs out and redirects to `/`; `/accounts/password_reset/` sends one email (in `mail.outbox`) with a working reset link for an existing address and shows the same "sent" page for an unknown address

### Implementation for User Story 2

- [X] T032 [US2] Implement `SignUpForm` (subclass of `UserCreationForm` for `accounts.User`, fields `email`, `password1`, `password2`, Persian labels, case-insensitive duplicate check) in `accounts/forms.py`, and an `EmailAuthenticationForm` with a Persian "ایمیل" label for the login view
- [X] T033 [US2] Implement `SignUpView` in `accounts/views.py` (`CreateView`; logs the user in after save and redirects to `settings.LOGIN_REDIRECT_URL`; redirects signed-in users away) and route it at `/accounts/signup/` as `accounts:signup` in `accounts/urls.py`; configure the built-in `LoginView` to use `EmailAuthenticationForm`
- [X] T034 [P] [US2] Create Persian Bootstrap templates `templates/accounts/signup.html`, `templates/registration/login.html` (with links to sign-up and password reset), `templates/registration/password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html`, `password_reset_email.html` and `password_reset_subject.txt`; every field has a visible `<label>` and errors use Bootstrap `invalid-feedback`
- [X] T035 [US2] Update the navbar in `templates/base.html`: signed-out → "ورود" and "ثبت‌نام"; signed-in → the user's email and a "خروج" button inside a POST form with `{% csrf_token %}`

**Checkpoint**: Accounts work on their own (quickstart scenarios 4–5).

---

## Phase 5: User Story 3 - Price alerts for buy/sell signals (Priority: P1)

**Goal**: Signed-in users create alerts on their own threshold X; after every successful read
the poller fires each armed alert once per crossing, re-arms it only when the price is strictly
back on the other side, and creates in-site notifications with an unread badge.

**Independent Test**: Create an "above, buy" alert just below the current price, run
`poll_prices --once` twice: exactly one notification and badge "۱"; invalid thresholds and a
21st active alert are refused (quickstart scenarios 6–9).

**Depends on**: US1 (`PriceReading`, `poll_prices`). Views can be tested with
`client.force_login`, so US2 is not required for the tests.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Write model tests in `alerts/tests/test_models.py`: new alert state is `armed`; `note` longer than 200 characters is invalid; a second `Notification` with the same (`alert`, `price_reading`) raises `IntegrityError`; deleting an alert keeps its notifications with `alert = NULL` and their copied values
- [X] T037 [P] [US3] Write evaluation tests in `alerts/tests/test_evaluation.py` covering every rule in FR-013–FR-015 and data-model.md state transitions: above fires at price ≥ X and below at price ≤ X; a triggered alert sends nothing while the price stays at or past X (including exactly X on many readings); above re-arms only at price < X and below only at price > X; an alert already true at creation fires on the next reading; paused alerts and alerts of inactive users are skipped and keep their state; several alerts of one user firing on one reading create one notification each; re-running evaluation on the same reading creates no duplicates; a failed reading evaluates nothing; 20,000 armed alerts evaluate in under 10 seconds (SC-006; mark the test with a `@tag("slow")`)
- [X] T038 [P] [US3] Write form tests in `alerts/tests/test_forms.py`: threshold accepts `"۲۷۱٬۱۶۵"`, `"271,165"`, `"٢٧١١٦٥"`; rejects `"-5"`, `"0"`, `"abc"`, `"12.5"` with Persian errors; a user with 20 alerts that are armed or triggered cannot create a 21st (paused alerts do not count); editing X or direction sets an armed/triggered alert to `armed`, editing only signal or note keeps the state, editing a paused alert keeps it paused
- [X] T039 [P] [US3] Write view tests in `alerts/tests/test_views.py`: anonymous users are redirected to login for every alerts and notifications page; list/create/edit/pause/resume/delete work for the owner and return 404 for another user's alert; resume beyond the 20 limit is refused with a message; `/notifications/` lists newest first, 20 per page, and shows signal, direction, X, note, price, trade time and created time; mark-one and mark-all set `read_at`; the disclaimer text appears on the alert pages and the notification list; `GET /notifications/unread-count.json` returns `{"unread": n}` and HTTP 401 `{"unread": null}` for anonymous users
- [X] T040 [P] [US3] Write a command test in `alerts/tests/test_poll_integration.py`: with a mocked Wallex price above X, `call_command("poll_prices", "--once")` twice creates exactly one notification for an armed "above" alert

### Implementation for User Story 3

- [X] T041 [US3] Create `PriceAlert` in `alerts/models.py`: `user` (FK → `settings.AUTH_USER_MODEL`, cascade, `related_name="alerts"`), `threshold` (`DecimalField(max_digits=20, decimal_places=0)`, validator `> 0`, "whole Toman, set by the user"), `direction` (choices `above` / `below`), `signal` (choices `buy` / `sell`), `note` (`CharField(max_length=200, blank=True)`), `state` (choices `armed` / `triggered` / `paused`, default `armed`), `last_triggered_at` (nullable), `created_at` / `updated_at`; index on (`state`, `direction`, `threshold`); Persian `verbose_name`s and choice labels ("فعال", "فعال‌شده — منتظر بازگشت قیمت", "متوقف")
- [X] T042 [US3] Create `Notification` in `alerts/models.py`: `user` (FK, cascade, `related_name="notifications"`), `alert` (FK → `PriceAlert`, `on_delete=SET_NULL`, nullable), `price_reading` (FK → `prices.PriceReading`, `on_delete=PROTECT`), copied `signal`, `direction`, `threshold`, `note`, `price`, `created_at` (indexed), `read_at` (nullable); `UniqueConstraint(fields=["alert", "price_reading"])`; `Meta.ordering = ["-created_at"]`; run `makemigrations alerts`
- [X] T043 [US3] Implement `alerts/evaluation.py` `evaluate_alerts(reading)`: return immediately unless `reading.status == "ok"`; inside `transaction.atomic()` load once the alerts with `state` in (`armed`, `triggered`) and `user__is_active=True`; fire armed alerts (create `Notification` with copied values, set `triggered` and `last_triggered_at`) and re-arm triggered alerts per FR-014/FR-015 using bulk queries; use `bulk_create(..., ignore_conflicts=True)` for notifications so a re-run never duplicates; return counts fired and re-armed
- [X] T044 [US3] Fill the `after_reading(reading)` step in `prices/management/commands/poll_prices.py` with a call to `alerts.evaluation.evaluate_alerts(reading)` and log the counts; update `prune_old_readings()` in `prices/services.py` to keep readings referenced by any `Notification`
- [X] T045 [US3] Implement `AlertForm` in `alerts/forms.py`: `threshold` as a `CharField` cleaned with `core.numbers.parse_toman` (must be > 0), `direction` and `signal` as radio choices with Persian labels, `note`; help text explaining any direction can be paired with buy or sell; the 20-alert limit check (armed + triggered, excluding the alert being edited); on save set `state = "armed"` when `threshold` or `direction` changed and the alert is not paused
- [X] T046 [US3] Implement the alert views in `alerts/views.py` (all `LoginRequiredMixin`, querysets filtered by `request.user`): `AlertListView` (shows "n / 20"), `AlertCreateView`, `AlertUpdateView`, `AlertDeleteView` (confirmation page), and POST-only `alert_pause` / `alert_resume` (resume refused with a message past the limit); routes per contracts/http-routes.md in `alerts/urls.py`
- [X] T047 [US3] Implement the notification views in `alerts/views.py`: `NotificationListView` (paginate by 20), POST-only `notification_read` and `notifications_read_all`, and `unread_count_json` (HTTP 401 `{"unread": null}` for anonymous users); routes `/notifications/`, `/notifications/<id>/read/`, `/notifications/read-all/`, `/notifications/unread-count.json` in `alerts/urls.py`
- [X] T048 [P] [US3] Create templates `templates/alerts/alert_list.html`, `alert_form.html`, `alert_confirm_delete.html` and `notification_list.html` with Bootstrap tables that collapse to cards under 576 px, state badges, the disclaimer "این هشدارها صرفاً اطلاع‌رسانی هستند و توصیهٔ مالی نیستند." as an `alert-secondary` block, unread rows highlighted, and every price and time through the `toman` and `jalali` filters
- [X] T049 [US3] Add `core/context_processors.py` `unread_notifications` (count for signed-in users, `None` otherwise), register it in `config/settings.py`, and add to the navbar in `templates/base.html` links "هشدارها" and "اعلان‌ها" with a `badge` showing the count (hidden at zero) carrying a `data-unread-badge` attribute
- [X] T050 [P] [US3] Write `static/js/notifications.js` (included in `base.html` only for signed-in users): every 60 s `fetch("/notifications/unread-count.json")`, update the badge, stop polling on HTTP 401, skip while the tab is hidden
- [X] T051 [US3] Add a link to the alerts page on the home card for signed-in users in `templates/core/home.html`; set `LOGIN_REDIRECT_URL = "alerts:list"` in `config/settings.py` and update the redirect expectations in `accounts/tests/test_views.py` to `alerts:list`

**Checkpoint**: Alerts and notifications work end to end (quickstart scenarios 6–9).

---

## Phase 6: User Story 4 - Admin panel (Priority: P2)

**Goal**: Staff manage users, alerts and notifications and see price-reading health in a dark,
blue-accented, right-to-left Django admin, with a warning banner when reading has stopped.

**Independent Test**: As a superuser, deactivate a test user: they cannot sign in and their
alerts stop firing; a normal user cannot open `/admin/` (quickstart scenarios 10–11).

**Depends on**: US1 (`PriceReading`) and US3 (`PriceAlert`, `Notification`) for their admin
pages; the user admin needs only Phase 2.

### Tests for User Story 4 ⚠️

- [X] T052 [P] [US4] Write admin tests in `accounts/tests/test_admin.py`, `alerts/tests/test_admin.py` and `prices/tests/test_admin.py`: a non-staff user is redirected away from `/admin/`; the user changelist searches by email and the deactivate/reactivate actions set `is_active`; alert admin filters by state/signal/direction, has pause/resume actions and no add permission; notification admin has no add permission; the price reading changelist shows the last successful read and the count of failures in the last 24 h; every admin page shows the warning banner when no successful read for more than 5 minutes and hides it otherwise

### Implementation for User Story 4

- [X] T053 [P] [US4] Register `accounts.User` in `accounts/admin.py` with a `UserAdmin` subclass adapted to email login (no `username`): `list_display` email, is_active, is_staff, date_joined; `search_fields = ["email"]`; `list_filter` is_active, is_staff; actions "غیرفعال کردن" and "فعال کردن"; add/change forms based on email
- [X] T054 [P] [US4] Register `PriceAlert` and `Notification` in `alerts/admin.py`: alert `list_display` user, threshold, direction, signal, state, last_triggered_at; `list_filter` state, signal, direction; `search_fields = ["user__email"]`; actions pause and resume; `has_add_permission` returns `False`. Notification `list_display` user, signal, price, created_at, read_at; `list_filter` read/unread (custom `SimpleListFilter`) and `created_at`; `search_fields = ["user__email"]`; `has_add_permission` returns `False`
- [X] T055 [P] [US4] Register `PriceReading` in `prices/admin.py`: `list_display` status, price, fetched_at, traded_at, error; `list_filter` status; read-only (no add or change); override `changelist_view` to pass `last_ok` and `failures_24h` to `templates/admin/prices/pricereading/change_list.html`, which shows them above the list
- [X] T056 [US4] Create `templates/admin/base_site.html` extending `admin/base.html`: Persian site header "پنل مدیریت هشدار قیمت تتر"; force the admin dark theme (`data-theme="dark"` on `<html>` and hide the theme toggle) and set the blue/black variables (`--primary`, `--secondary`, `--link-fg`, `--body-bg`, `--darkened-bg`) in `static/css/admin.css` linked from the `extrastyle` block; show the price-reading warning banner from a `{% price_reading_warning %}` inclusion tag defined in `prices/templatetags/price_status.py`

**Checkpoint**: All four stories work independently.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates from the constitution and the quickstart.

- [X] T057 [P] Write `README.md` with a short Persian and English description, setup and run commands that point to `specs/001-usdt-price-alerts/quickstart.md`, and the two launch risks from spec Assumptions (Wallex reachability from the server, Wallex terms of use)
- [X] T058 [P] Review every template for semantic HTML (one `<h1>` per page, headings in order, labelled fields, `alt` text) and fix issues in `templates/`
- [X] T059 Check `/`, `/accounts/signup/`, `/accounts/login/`, `/alerts/`, `/alerts/new/`, `/notifications/` and `/admin/` at 360 px and desktop widths with JavaScript on and off; fix layout issues in `static/css/app.css` or the templates
- [X] T060 Run the constitution quality gates and fix any failure: `python manage.py test`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `DJANGO_DEBUG=False DJANGO_SECRET_KEY=<random 50 chars> DJANGO_ALLOWED_HOSTS=example.com python manage.py check --deploy`
- [X] T061 Walk through all 13 scenarios in `specs/001-usdt-price-alerts/quickstart.md` and record the result of each in a "Validation results" section at the end of that file

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every story. T007 must come before T009.
- **US1 (Phase 3)** and **US2 (Phase 4)**: each depends only on Phase 2; they can run in
  parallel.
- **US3 (Phase 5)**: depends on Phase 2 and US1 (`PriceReading`, `poll_prices`).
- **US4 (Phase 6)**: T053 depends only on Phase 2; T054–T056 depend on US1 and US3.
- **Polish (Phase 7)**: after the stories you want to ship.

```text
Setup → Foundational ─┬─ US1 ──┬─ US3 ──┐
                      │        └────────┼─ US4 ─ Polish
                      └─ US2 ───────────┘
```

### Within Each Story

- Tests first, and they must fail before implementation.
- Models (and their migration) before services, services before views, views before templates
  and scripts.
- Finish a story and pass its checkpoint before moving on.

### Parallel Opportunities

- Setup: T003, T004, T005.
- Foundational: T008, T010–T014 after T007.
- US1: tests T018–T022 together; T027 and T029 after T025.
- US2: T030 and T031 together; T034 alongside T032–T033.
- US3: tests T036–T040 together; T048 and T050 alongside the views.
- US4: T052 first; T053, T054, T055 together.
- US1 and US2 as whole phases, by different people.

---

## Parallel Example: User Story 3

```bash
# Write all US3 tests together:
Task: "Write model tests in alerts/tests/test_models.py"
Task: "Write evaluation tests in alerts/tests/test_evaluation.py"
Task: "Write form tests in alerts/tests/test_forms.py"
Task: "Write view tests in alerts/tests/test_views.py"
Task: "Write a command test in alerts/tests/test_poll_integration.py"

# After the views exist, build the front end together:
Task: "Create templates in templates/alerts/"
Task: "Write static/js/notifications.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup.
2. Phase 2: Foundational.
3. Phase 3: US1 — the public live price page.
4. **Stop and validate** with quickstart scenarios 1–3.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → public price page (MVP).
3. US2 → accounts.
4. US3 → alerts and notifications (the core value).
5. US4 → admin panel.
6. Polish → quality gates and the full quickstart.

### Parallel Team Strategy

After Phase 2: developer A takes US1 then US3; developer B takes US2 then US4 (T053 first,
T054–T056 once US1 and US3 are in).

---

## Notes

- [P] = different files, no dependency on unfinished tasks.
- Commit after each task or logical group.
- The reviewer-owned checklist `checklists/alerts.md` is still unchecked; `/speckit-implement`
  reads it as a gate.
