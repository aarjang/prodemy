# Data Model: USDT Price Alerts

All prices are whole Toman stored as `Decimal` (`max_digits=20, decimal_places=0`). All
times are timezone-aware (stored UTC, shown in Asia/Tehran, Jalali calendar).

## User (`accounts.User`)

Extends Django's `AbstractUser`.

| Field | Type | Rules |
|-------|------|-------|
| email | email | required, unique (case-insensitive: stored lowercased); `USERNAME_FIELD` |
| password | hashed | Django password validators |
| is_active | bool | `False` = deactivated: cannot sign in, alerts not evaluated |
| is_staff | bool | `True` = admin role, can open the admin panel |
| date_joined | datetime | auto |

`username` is removed; `REQUIRED_FIELDS = []`.

## PriceReading (`prices.PriceReading`)

One attempt to read the USDT/Toman price from Wallex.

| Field | Type | Rules |
|-------|------|-------|
| fetched_at | datetime | when the attempt finished; indexed |
| status | choice | `ok` or `failed` |
| price | decimal, nullable | required and > 0 when `ok`; null when `failed` |
| traded_at | datetime, nullable | time of the last Wallex trade; required when `ok` |
| error | text | short failure reason when `failed` (timeout, HTTP status, bad data) |

- Latest price = newest row with `status = ok`.
- Stale when `now - latest ok fetched_at > 5 minutes` (FR-003).
- Retention: rows older than 30 days are deleted unless a Notification references them.
- Ordering: `-fetched_at`.

## PriceAlert (`alerts.PriceAlert`)

| Field | Type | Rules |
|-------|------|-------|
| user | FK → User | owner; cascade delete |
| threshold | decimal | > 0, whole Toman, set by the user (FR-010) |
| direction | choice | `above` or `below` |
| signal | choice | `buy` or `sell` |
| note | text, optional | max 200 characters |
| state | choice | `armed`, `triggered`, `paused`; default `armed` |
| last_triggered_at | datetime, nullable | set when it fires |
| created_at / updated_at | datetime | auto |

- Limit: at most 20 alerts per user with `state != paused` (FR-018), checked in the form and on resume.
- Index on (`state`, `direction`, `threshold`) for evaluation queries.

### State transitions

```text
            create
              │
              ▼
   ┌────── armed ──────┐ price crosses X (above: p >= X / below: p <= X)
   │          ▲        │  → create Notification, set last_triggered_at
 pause        │        ▼
   │     re-arm      triggered
   │  (above: p < X / below: p > X)
   ▼                   │
 paused ◄──── pause ───┘
   │
 resume → armed
```

- Editing `threshold` or `direction` resets the state to `armed` (unless paused); editing
  only `signal` or `note` keeps the state (FR-012).
- Alerts of inactive users are skipped during evaluation and keep their state; crossings
  while inactive are never notified later (FR-021).

## Notification (`alerts.Notification`)

| Field | Type | Rules |
|-------|------|-------|
| user | FK → User | recipient (copied from the alert); cascade delete |
| alert | FK → PriceAlert, nullable | set null if the alert is deleted, so history remains |
| price_reading | FK → PriceReading | the reading that triggered it; protect delete |
| signal / direction / threshold / note | copied values | snapshot of the alert at firing time (FR-017) |
| price | decimal | price at firing time |
| created_at | datetime | auto; indexed |
| read_at | datetime, nullable | set when the user marks it read |

- Unique constraint (`alert`, `price_reading`) → no duplicates per crossing (SC-003).
- Unread count = notifications of the user with `read_at IS NULL`.
- Delivery is in-site only: a notification is visible as soon as it is created; its only status is read or unread.
- Ordering: `-created_at`.

## Relationships

```text
User 1 ──── * PriceAlert 1 ──── * Notification * ──── 1 PriceReading
  └──────────────────────────────── * Notification
```
