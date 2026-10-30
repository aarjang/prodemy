# Feature Specification: USDT Price Alerts

**Feature Branch**: `001-usdt-price-alerts`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "من میخوام یه اپلیکیشن بنویسم که بره از ولکس برای من قیمت تتر رو بخونه و بیاد یک سری فانکشن داشته باشه توش. برای مثال قیمت رو اگر بالای عدد X بود به من یک نوتیفیکیشن بده که میتونم بخرم، اگر پایین قیمت X بود بتونم بفروشم. یک ادمین پنلی مثلا میخوام داشته باشه، یوزرها هم بتونن باهاش مثلا ثبت نام بکنن یا حالا فعلا همینا داشته بریم بعد."

(Summary: a website that reads the USDT (Tether) price from the Wallex exchange, lets users
sign up, notifies a user when the price goes above or below a threshold they set — as a
buy or sell signal — and offers an admin panel.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the current USDT price (Priority: P1)

A visitor opens the website and sees the last traded USDT price on Wallex, the time the
site read it, and the time of that trade.

**Why this priority**: Every other feature depends on reliably reading the price. On its
own, a page showing the live price already gives value.

**Independent Test**: Open the home page and compare the shown price with Wallex's last
USDT/Toman trade at the same moment; both times are shown and the read time refreshes as new
readings arrive.

**Acceptance Scenarios**:

1. **Given** the price source is reachable, **When** a visitor opens the home page,
   **Then** they see the last traded USDT price in Toman, the time it was read, and the time
   of the trade.
2. **Given** the page is open, **When** a new price is read, **Then** the shown price and
   read time change without the visitor having to do anything beyond the page's normal
   refresh behavior.
3. **Given** no successful read for more than 5 minutes, **When** a visitor opens the page,
   **Then** they see the last known price clearly marked as stale with its read time.
4. **Given** the last trade on Wallex is more than 60 minutes old, **When** a visitor opens
   the page, **Then** the price is shown with a note that there have been no recent trades.
5. **Given** no price has ever been read, **When** a visitor opens the page, **Then** they
   see a message that the price is not available yet instead of a number.

---

### User Story 2 - Sign up and sign in (Priority: P1)

A visitor creates an account with their email and a password, then signs in and out.

**Why this priority**: Personal price alerts need an account to belong to and a place to
deliver notifications.

**Independent Test**: Register a new account, sign out, sign back in, and reach the
personal dashboard.

**Acceptance Scenarios**:

1. **Given** a visitor without an account, **When** they submit a valid email and password,
   **Then** an account is created and they are signed in.
2. **Given** an email that is already registered, **When** someone tries to sign up with
   it, **Then** sign-up is refused with a clear message.
3. **Given** a registered user, **When** they enter wrong credentials, **Then** sign-in is
   refused without revealing which field was wrong.
4. **Given** a user who forgot their password, **When** they request a reset, **Then** they
   receive a reset link by email and can set a new password.

---

### User Story 3 - Price alerts for buy/sell signals (Priority: P1)

A signed-in user creates alerts. Each alert has a threshold price X, a direction ("price goes
above" or "price goes below"), and a signal of "buy" or "sell". Any combination of direction
and signal is allowed, and the alert form explains this in one line. When the USDT price
crosses X in that direction, the user gets a notification telling them it may be a good
time to buy or sell. Signals are informational only.

**Why this priority**: This is the core value of the product.

**Independent Test**: Create an alert just above the current price, wait for (or simulate)
the price crossing it, and confirm one notification arrives with the alert's details.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they create an alert "notify me as a buy signal when
   the price goes above X", **Then** the alert appears in their alert list as armed.
2. **Given** an armed "above X" alert, **When** a newly read price is at or above X, **Then**
   the user receives one notification and the alert becomes triggered.
3. **Given** an armed "below X" alert, **When** a newly read price is at or below X, **Then**
   the user receives one notification and the alert becomes triggered.
4. **Given** a triggered alert, **When** the price stays at or past X (including exactly X)
   on later readings, **Then** no further notifications are sent for that alert.
5. **Given** a triggered "above X" alert, **When** a newly read price is below X, **Then** the
   alert becomes armed again; for a triggered "below X" alert this happens when the price is
   above X.
6. **Given** a user's alert list, **When** they edit, pause, resume or delete an alert,
   **Then** the change takes effect from the next price check.
7. **Given** a user, **When** they open their notification history, **Then** they see every
   notification for them, newest first, including notifications from alerts they have since
   deleted.
8. **Given** a user on the alert pages or notification list, **When** they view them,
   **Then** they see a short notice that signals are informational and not financial advice.

---

### User Story 4 - Admin panel (Priority: P2)

An administrator signs in to an admin panel to manage users, see and manage all alerts,
view notifications, and see the health of price reading (last successful read, recent
failures).

**Why this priority**: Needed to operate the service, but users get value without it.

**Independent Test**: Sign in as an admin, deactivate a test user, and confirm that user can
no longer sign in and their alerts stop firing.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they open the admin panel, **Then** they can list, search,
   deactivate and reactivate users.
2. **Given** an admin, **When** they view alerts or notifications, **Then** they can filter
   them by user and state, pause, resume or delete alerts, and delete notifications.
3. **Given** an admin, **When** they view price status, **Then** they see the last successful
   read time, the failures in the last 24 hours and the reason for each.
4. **Given** no successful read for more than 5 minutes, **When** an admin opens any admin
   page, **Then** a warning banner says price reading has stopped and since when.
5. **Given** a regular user, **When** they try to open the admin panel, **Then** access is
   denied.

---

### Edge Cases

- The price source is down, slow, rate-limits the site, or returns invalid data: keep the
  last valid price, mark it stale after 5 minutes, record the failure with its reason, and
  never evaluate alerts on a failed read.
- The price source changes its response format: this is treated as invalid data, so it
  shows up as failed reads and, after 5 minutes, as the admin warning.
- The price jumps past the threshold between two reads: the alert still fires once.
- The price stays exactly at X or moves back and forth around X: an alert fires once and
  only re-arms when the price is strictly on the other side of X.
- A crossing happens and reverses while price reading is down: it is not notified; only
  prices the site actually read count.
- Several alerts of the same user meet their condition on the same reading: each alert
  sends its own notification.
- A user creates or resumes an alert whose condition is already true: it fires on the next
  price check.
- A user edits or deletes an alert while a price check is running: the check uses the alert
  as it was when the check started, and the change applies from the next check.
- Threshold values that are zero, negative, or not numbers are rejected.
- A user has 20 alerts that are armed or triggered: creating or resuming another is refused.
- A deactivated user's alerts are not evaluated; crossings while the user is inactive are
  not notified later.

## Requirements *(mandatory)*

### Functional Requirements

**Price reading**

- **FR-001**: System MUST read the last traded USDT/Toman price from Wallex at a regular
  interval of at most 1 minute. "Price" everywhere in this spec means this last traded price.
- **FR-002**: System MUST store every read attempt with its time for 30 days: successful
  reads with the price and the trade time, failed reads with the reason. This history is used
  for the admin price status and for notifications; no price charts are in scope.
- **FR-003**: System MUST show on a public page the latest price, the time it was read and
  the time of the trade. It MUST mark the price as stale when no successful read has happened
  for more than 5 minutes, and MUST show a "no recent trades" note when the trade is more than
  60 minutes old. The 5-minute stale limit is longer than the read interval on purpose, so a
  few failed reads in a row do not flash a warning.
- **FR-004**: A read MUST count as failed when the source cannot be reached, answers with an
  error or a rate-limit response, returns data in an unexpected format, or returns a price
  that is not a number, is zero or negative, or has a missing or future trade time. Failed
  reads MUST be recorded and MUST NOT be used to evaluate alerts.
- **FR-005**: System MUST NOT read from Wallex more often than once every 30 seconds on
  average, and MUST wait at least 60 seconds between attempts after a rate-limit response or
  after 5 failed reads in a row, until a read succeeds.
- **FR-006**: Prices from Wallex that carry decimals MUST be rounded to the nearest whole
  Toman (halves rounded up) before they are stored, shown or compared.

**Accounts**

- **FR-007**: Visitors MUST be able to sign up with an email and password; emails MUST be
  unique.
- **FR-008**: Users MUST be able to sign in, sign out, and reset a forgotten password by
  email.
- **FR-009**: Only signed-in users MUST be able to create or view their own alerts and
  notifications; users MUST NOT see other users' data.

**Alerts and notifications**

- **FR-010**: Users MUST be able to create an alert with a threshold price X that they
  choose themselves (any positive whole Toman amount), a direction (above / below) and a
  signal (buy / sell), plus an optional note of up to 200 characters.
- **FR-011**: Each alert MUST be in exactly one state: **armed** (waiting for a crossing),
  **triggered** (has fired, waiting for the price to return) or **paused** (not evaluated).
  New alerts start armed.
- **FR-012**: Users MUST be able to list, edit, pause, resume and delete their alerts.
  Changing X or the direction of an armed or triggered alert MUST set it to armed; changing
  only the signal or note MUST keep its state; resuming a paused alert MUST set it to armed.
- **FR-013**: After every successful read, System MUST evaluate all armed and triggered
  alerts of active users against that price, and only that price. Evaluation MUST finish
  within 10 seconds of the read.
- **FR-014**: An armed alert MUST fire when the price is at or beyond X in its direction
  (above: price ≥ X; below: price ≤ X). Firing MUST create exactly one notification for that
  alert and set the alert to triggered. Best bid and ask prices are not used. The age of the
  last trade does not block firing; the notification shows the trade time.
- **FR-015**: A triggered alert MUST return to armed only when the price is strictly on the
  other side of X (above: price < X; below: price > X). A triggered alert MUST NOT create
  further notifications.
- **FR-016**: Notifications MUST be delivered inside the website only: a notification list
  plus an unread-count badge visible on every page while signed in. Each notification MUST
  show the signal, direction, threshold X, the alert's note, the price, the trade time and the
  time it was created; users MUST be able to mark notifications as read, one at a time or all
  at once.
- **FR-017**: System MUST keep each user's notification history, newest first. Notifications
  MUST keep the alert's values from the moment they were created and MUST remain when the
  alert is later edited or deleted.
- **FR-018**: Each user MUST have at most 20 alerts that are armed or triggered; paused
  alerts do not count. Creating or resuming an alert beyond this limit MUST be refused with a
  message.
- **FR-019**: The alert pages and the notification list MUST show a short notice that
  signals are informational only and are not financial advice.
- **FR-020**: The system MUST only notify; it MUST NOT place buy or sell orders on any
  exchange.

**Admin**

- **FR-021**: Admins MUST be able to manage users: list, search by email, deactivate and
  reactivate. A deactivated user cannot sign in and their alerts are not evaluated; on
  reactivation their alerts keep the state they had and are evaluated from the next read.
- **FR-022**: Admins MUST be able to view and filter all alerts (by user, state, direction
  and signal) and pause, resume or delete them, and view, filter (by user and read/unread)
  and delete notifications. Admins cannot create alerts for users.
- **FR-023**: Admins MUST be able to see price reading status: the last successful read and
  the failed reads of the last 24 hours with their reasons.
- **FR-024**: When no successful read has happened for more than 5 minutes, every admin page
  MUST show a warning banner with the time of the last successful read.
- **FR-025**: Only users with the admin role MUST be able to access the admin panel.

**Interface**

- **FR-026**: The website interface MUST be in Persian with a right-to-left layout on every
  page, including the admin panel.
- **FR-027**: Prices MUST be shown in Toman with thousands separators, and dates and times
  MUST be shown in the Persian (Solar Hijri) calendar, Tehran time.
- **FR-028**: Every page, including the admin panel, MUST use a single dark theme; there is
  no light mode or theme switch.
- **FR-029**: The color scheme MUST be black (and near-black shades) for backgrounds with
  blue as the accent color for links, buttons, highlights and the active navigation item.
  Text and controls MUST keep a contrast ratio of at least 4.5:1 against their background.

### Key Entities

- **User**: a person with an account; email, password, active/inactive status, admin or
  regular role.
- **Price Reading**: one attempt to read the USDT price from Wallex: the time of the attempt
  and either the price in Toman with its trade time, or the reason it failed.
- **Price Alert**: belongs to a user; threshold X, direction (above/below), signal
  (buy/sell), note, state (armed, triggered, paused), time it last fired.
- **Notification**: created for a user when an alert fires; copy of the alert's signal,
  direction, threshold and note, the price reading that caused it, created time, read or
  unread.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: While Wallex is reachable, in at least 99% of spot checks the price on the
  website equals Wallex's last USDT/Toman trade price as of a read made no more than 1 minute
  earlier.
- **SC-002**: 95% of notifications appear in the user's notification list and badge within
  2 minutes of the time of the Wallex trade that caused the crossing.
- **SC-003**: Over any 30-day period, each alert has exactly one notification per change
  from armed to triggered, and never more than one notification for the same alert and
  price reading.
- **SC-004**: A new visitor can sign up and create their first alert in under 3 minutes.
- **SC-005**: An admin can find a user and deactivate them in under 1 minute.
- **SC-006**: All alerts are evaluated within 10 seconds of a read with 20,000 armed or
  triggered alerts in the system.

## Assumptions

- "Tether price" means the last traded price of Wallex's USDT/Toman market (`USDTTMN`).
- Wallex data source (checked 2026-10-30 against Wallex's live public API; its developer
  docs site did not render): public market data is readable without an API key or trading
  account. The market list gives, per market, the last traded price, best bid and ask, and
  24-hour high, low and change; prices are in whole Toman (precision 0). The market list
  carries no time for the last price, but the recent-trades data for a market includes a
  timestamp for each trade. Wallex reports a request limit of 600 per window; live streaming
  could not be confirmed and is not used.
- **Risk**: Wallex may refuse requests from servers outside Iran. Before launch, the
  production server must be confirmed to reach Wallex.
- **TODO(owner)**: Wallex's terms of use for automated reading of public data have not been
  checked; the project owner needs to confirm them before launch. The reading rate (FR-005) is
  low.
- The user's "above X → buy, below X → sell" is modelled generally: each alert chooses its
  direction and signal, so either combination is possible.
- The service only sends notifications; trading stays manual on Wallex (FR-020).
- Email/password sign-up is used; social sign-in and phone/SMS verification are out of scope
  for this version.
- Email verification on sign-up is not required in this version (password reset email still
  is).
- Price charts and history longer than 30 days are out of scope.
- Other coins and other exchanges are out of scope for this version.
- Notifications reach users only while they visit the site; email, Telegram, SMS and push
  notifications are out of scope for this version. Email is used only for password reset.
- Persian digits or Western digits in numbers is a presentation detail left to planning.

## Clarifications

### Session 2026-10-30

- Q: How should a user receive a buy or sell notification? → A: Inside the website only
  (notification list and unread badge).
- Q: What language should the website be in? → A: Persian, right-to-left.
- Q: Which Wallex price should alerts compare against the threshold? → A: The last traded
  price, for every alert; it is also the price shown on the site.
- Q: What should the site look like? → A: Dark mode on every page, black and blue colors.
- Q: Who sets the alert threshold X? → A: Each user sets X themselves for every alert.
