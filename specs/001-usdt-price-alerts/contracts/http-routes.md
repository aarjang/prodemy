# Contract: HTTP Routes

All HTML pages extend `base.html` (`lang="fa" dir="rtl" data-bs-theme="dark"`). "Auth" =
sign-in required; anonymous users are redirected to `/accounts/login/?next=…`. All POSTs
require a CSRF token. Users can only reach their own alerts and notifications; another
user's id returns **404**.

## Public pages

| Method | Path | Name | Behavior |
|--------|------|------|----------|
| GET | `/` | `core:home` | Latest price card: price, "read at", "last trade at", stale badge when no successful read for > 5 min, "no recent trades" note when the trade is > 60 min old, empty state when no reading exists yet. Signed-in users also see a link to their alerts. |

## Accounts (`accounts` app + Django auth views)

| Method | Path | Name | Behavior |
|--------|------|------|----------|
| GET/POST | `/accounts/signup/` | `accounts:signup` | Email + password + confirm. Success → signed in, redirect to `LOGIN_REDIRECT_URL` (`core:home` until US3, then `alerts:list`). Duplicate email → form error. |
| GET/POST | `/accounts/login/` | `login` | Email + password. Wrong credentials → one generic error. Inactive user → refused. |
| POST | `/accounts/logout/` | `logout` | Signs out, redirect to `/`. |
| GET/POST | `/accounts/password_reset/` … `/accounts/reset/done/` | Django defaults | Reset email with link; always shows the same "sent" page whether or not the email exists. |

## Alerts and notifications (`alerts` app, Auth)

| Method | Path | Name | Behavior |
|--------|------|------|----------|
| GET | `/alerts/` | `alerts:list` | User's alerts with threshold, direction, signal, state, last triggered; active count "n / 20". |
| GET/POST | `/alerts/new/` | `alerts:create` | Form: threshold (Persian or Western digits, separators allowed), direction, signal, note. Rejects ≤ 0, non-numeric, or a 21st active alert. |
| GET/POST | `/alerts/<id>/edit/` | `alerts:edit` | Same form; changing threshold or direction re-arms. |
| POST | `/alerts/<id>/pause/` | `alerts:pause` | state → paused. |
| POST | `/alerts/<id>/resume/` | `alerts:resume` | state → armed (subject to the 20 limit). |
| GET/POST | `/alerts/<id>/delete/` | `alerts:delete` | Confirmation page, then delete. |
| GET | `/notifications/` | `alerts:notifications` | Paginated history (20 per page), newest first, unread highlighted. |
| POST | `/notifications/<id>/read/` | `alerts:notification_read` | Marks one as read. |
| POST | `/notifications/read-all/` | `alerts:notifications_read_all` | Marks all as read. |

The alert pages and the notification list show the notice "این هشدارها صرفاً اطلاع‌رسانی هستند و توصیهٔ مالی نیستند." (FR-019). A notification row shows signal, direction, X, note, price, trade time and created time (FR-016).

Every successful POST redirects (Post/Redirect/Get) and shows a Django message in Persian.

## JSON helpers (progressive enhancement only)

### `GET /prices/latest.json` — public

```json
{
  "price": 271165,
  "price_display": "۲۷۱٬۱۶۵",
  "fetched_at": "2026-10-30T07:27:00Z",
  "traded_at": "2026-10-29T20:02:29Z",
  "fetched_at_display": "۸ آبان ۱۴۰۵، ۱۰:۵۷",
  "traded_at_display": "۷ آبان ۱۴۰۵، ۲۳:۳۲",
  "stale": false,
  "no_recent_trades": false
}
```

When no successful reading exists: HTTP 200 with `{"price": null, "stale": true}`.
Response header `Cache-Control: no-store`.

### `GET /notifications/unread-count.json` — Auth

```json
{ "unread": 3 }
```

Anonymous → HTTP 401 `{"unread": null}` (no redirect, so the script can stop polling).

## Admin

| Path | Access | Contents |
|------|--------|----------|
| `/admin/` | `is_staff` only; others redirected to the admin login | Dark, blue-accented, RTL Django admin |
| Users | list/search by email; filter active/staff; actions: deactivate, reactivate |
| Price alerts | list with user, threshold, direction, signal, state; filter by user/state/signal/direction; search by user email; actions: pause, resume, delete; no add button (FR-022) |
| Notifications | list with user, price, created, read; filter by read/unread and date; search by user email; action: delete; no add button |
| Warning banner | every admin page | when no successful read for > 5 min: "price reading stopped since …" with the last successful read time (FR-024) |
| Price readings | list with status, price, fetched_at, traded_at, error; filter by status; the changelist header shows last successful read and failures in the last 24 h (FR-023) |
