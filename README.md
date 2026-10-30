# هشدار قیمت تتر (Prodemy)

وب‌سایت فارسی و راست‌به‌چپ که آخرین قیمت معاملهٔ تتر/تومان را از صرافی والکس می‌خواند،
آن را به‌صورت زنده نمایش می‌دهد و به کاربران ثبت‌نام‌شده اجازه می‌دهد روی قیمت دلخواه
خود هشدار خرید یا فروش بسازند. وقتی قیمت از آستانهٔ هشدار عبور کند، یک اعلان داخل
سایت ساخته می‌شود — دقیقاً یک بار برای هر عبور. سیگنال‌ها صرفاً اطلاع‌رسانی هستند و
سایت هیچ معامله‌ای انجام نمی‌دهد.

A Persian (RTL, dark-themed) Django site that reads the last traded USDT/Toman price from
the Wallex exchange, shows it live, and lets registered users create buy/sell alerts on
their own thresholds. Crossings create in-site notifications, exactly once per crossing.

## Stack

Python 3.12 · Django 5.2 LTS · Bootstrap 5.3 RTL (vendored) · vanilla JavaScript ·
SQLite in development, PostgreSQL in production.

## Setup & run

Full setup, run and validation steps live in
[specs/001-usdt-price-alerts/quickstart.md](specs/001-usdt-price-alerts/quickstart.md).
In short (with [uv](https://docs.astral.sh/uv/), which this repo was set up with):

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env          # then set DJANGO_SECRET_KEY and DJANGO_DEBUG=True
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
```

Two processes:

```bash
.venv/bin/python manage.py runserver
```

```bash
.venv/bin/python manage.py poll_prices
```

## Quality gates (must all pass)

```bash
.venv/bin/python manage.py test
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

and with production settings: `DJANGO_DEBUG=False DJANGO_SECRET_KEY=<random>
DJANGO_ALLOWED_HOSTS=<host> .venv/bin/python manage.py check --deploy`.

## Before launch (open risks)

- **Wallex reachability**: Wallex may refuse requests from servers outside Iran. Confirm the
  production server can reach `https://api.wallex.ir/v1/trades?symbol=USDTTMN`.
- **Wallex terms of use**: automated reading of public market data has not been cleared with
  Wallex's terms; the project owner must confirm this (the polling rate is one request per
  30 seconds).

## Project documents

Spec, plan, research, data model, contracts and tasks:
[specs/001-usdt-price-alerts/](specs/001-usdt-price-alerts/).
