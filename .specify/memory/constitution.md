<!--
Sync Impact Report
- Version change: (unversioned template) → 1.0.0
- Modified principles (template placeholders → defined):
  - [PRINCIPLE_1_NAME] → I. Django-First Backend
  - [PRINCIPLE_2_NAME] → II. Vanilla Frontend with Bootstrap
  - [PRINCIPLE_3_NAME] → III. Test-Backed Changes
  - [PRINCIPLE_4_NAME] → IV. Secure by Default
  - [PRINCIPLE_5_NAME] → V. Responsive, Accessible & Simple
- Added sections: Technology Stack & Constraints; Development Workflow & Quality Gates
- Removed sections: none
- Templates: not modified (dependent templates read the constitution at runtime)
- Deferred TODOs: none
-->

# Prodemy Constitution

## Core Principles

### I. Django-First Backend

- The website MUST be built with Django as its only server-side web framework.
- Pages MUST be server-rendered with the Django template language; templates MUST extend a
  shared base layout (`base.html`) rather than duplicating page chrome.
- Django built-ins (ORM, migrations, auth, admin, forms, messages, static files) MUST be used
  before any third-party package that duplicates them. Every added dependency MUST be pinned
  and justified in the feature plan.
- Code MUST be organized into focused Django apps, each with a single clear responsibility.
- Every schema change MUST ship as a committed Django migration.

**Rationale**: One framework with batteries included keeps the stack small, predictable and
easy to maintain.

### II. Vanilla Frontend with Bootstrap

- The UI MUST be written in plain HTML, CSS and JavaScript. Frontend frameworks and
  libraries (React, Vue, Angular, Svelte, jQuery, Alpine, htmx, Tailwind, etc.) MUST NOT be
  used.
- Bootstrap 5 MUST be the component and layout system: grid, utilities and components
  (navbar, cards, forms, modals, alerts, etc.) are used before writing custom equivalents.
- Custom styling MUST live in project CSS files loaded after Bootstrap and SHOULD extend it
  through Bootstrap's CSS variables and utility classes rather than overriding it wholesale.
- JavaScript MUST be vanilla ES modules or plain scripts, served through Django's static
  files. No frontend build step (bundler, transpiler) is required to run the site.
- Inline `style` attributes and inline `<script>` blocks MUST NOT be used except for
  Django-provided values that cannot be placed in a static file.
- JavaScript MUST be progressive enhancement: core content and forms MUST work with
  JavaScript disabled.

**Rationale**: Plain web standards plus Bootstrap give a consistent, professional look with
no toolchain lock-in and minimal complexity.

### III. Test-Backed Changes

- Every model, form and view MUST have automated tests using Django's test framework
  (`django.test.TestCase` / `Client`).
- A change MUST NOT be merged while `python manage.py test` fails.
- Bug fixes MUST include a test that reproduces the bug.

**Rationale**: Server-rendered pages are easy to test end to end with Django's test client;
tests keep regressions out as the site grows.

### IV. Secure by Default

- Django's security protections (CSRF, auto-escaping, clickjacking protection, password
  hashing) MUST stay enabled; disabling one requires a written justification in the plan.
- Secrets (`SECRET_KEY`, database credentials, API keys) MUST come from environment
  variables and MUST NOT be committed to the repository.
- Production MUST run with `DEBUG = False`, an explicit `ALLOWED_HOSTS`, and HTTPS-related
  settings enabled; `python manage.py check --deploy` MUST pass before release.
- All user input MUST be validated through Django forms or model validation.
- Third-party static assets (e.g. Bootstrap) MUST be served locally from static files or
  from a CDN pinned to an exact version with Subresource Integrity (`integrity`) attributes.

**Rationale**: Django's defaults are strong; the main risks come from turning them off or
leaking configuration.

### V. Responsive, Accessible & Simple

- Every page MUST be responsive (mobile-first with the Bootstrap grid) and usable from
  360px wide upward without horizontal scrolling.
- Markup MUST be semantic HTML5 (landmarks, headings in order, labelled form fields, `alt`
  text on images) and SHOULD meet WCAG 2.1 AA, including color contrast.
- Solutions MUST start with the simplest approach that meets the spec (YAGNI); added
  complexity MUST be justified in the plan's complexity tracking.

**Rationale**: A website is judged by how it works for every visitor on every device, and
simple code is what keeps it that way.

## Technology Stack & Constraints

- **Language**: Python 3 (current supported release); dependencies pinned in
  `requirements.txt`.
- **Backend**: Django (current LTS release), Django template language.
- **Frontend**: HTML5, CSS3, vanilla JavaScript (ES2015+), Bootstrap 5.
- **Database**: SQLite for local development; the production database is chosen per feature
  plan and MUST be accessed only through the Django ORM.
- **Static files**: collected with `collectstatic`; project assets organized under
  `static/css/`, `static/js/` and `static/img/`.
- **Prohibited**: JavaScript frameworks and SPA architectures, CSS frameworks other than
  Bootstrap, and frontend build pipelines unless the constitution is amended.

## Development Workflow & Quality Gates

- Work follows the Spec Kit flow: specify → (clarify) → plan → tasks → implement.
- Each plan MUST include a Constitution Check confirming compliance with Principles I–V and
  listing any justified deviations.
- Before a change is considered done:
  1. `python manage.py test` passes.
  2. `python manage.py check` passes, and `makemigrations --check` reports no missing
     migrations.
  3. Affected pages are checked at mobile and desktop widths.
  4. No secrets or debug settings are committed.

## Governance

- This constitution supersedes other project practices; where they conflict, it wins.
- Amendments are made through `/speckit-constitution`, MUST state the reason for the change,
  and MUST update the version and Last Amended date.
- Versioning follows semantic versioning: MAJOR for removing or redefining a principle,
  MINOR for adding a principle or section or materially expanding guidance, PATCH for
  clarifications and wording fixes.
- Every plan and code review MUST verify compliance with this constitution; any deviation
  MUST be documented and justified, or the work is revised.

**Version**: 1.0.0 | **Ratified**: 2026-10-30 | **Last Amended**: 2026-10-30
