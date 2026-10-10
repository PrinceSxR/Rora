# Spec: Registration

## Overview
Make the existing registration form work. Right now `GET /register` renders
`register.html`, but submitting the form goes nowhere because no route accepts
`POST /register`. This step adds server-side handling: validate the submitted
name, email and password, reject duplicate emails, hash the password with
werkzeug, insert the new row into `users`, and send the user to the login page
with a success message. It is the first feature that writes user data. The rest
of the auth flow builds on it: Step 3 (login/logout) needs real accounts to log
into. This step does **not** log the user in or create a session. That belongs
to Step 3.

## Depends on
- **Step 1 — Database setup** (complete): `users` table with `UNIQUE` email,
  `get_db()` with `PRAGMA foreign_keys = ON`, and `init_db()` called on startup.

## Routes
- `GET /register` — render the empty registration form — public (already
  exists; it gets merged into the same view function as POST)
- `POST /register` — validate the form, create the user, flash a success
  message and redirect to `GET /login`. On validation failure, re-render
  `register.html` with an error message and the previously entered name and
  email, using HTTP status 400 — public

Use one view function: `@app.route("/register", methods=["GET", "POST"])`.

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email UNIQUE`,
`password_hash`, `created_at`) already covers registration.

New helpers in `database/db.py` (no schema change):
- `get_user_by_email(email)` — returns the `sqlite3.Row` or `None`
- `create_user(name, email, password)` — hashes the password with
  `generate_password_hash`, inserts the row with a parameterised query, and
  returns the new user's `id`

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html`
    - change `action="/register"` to `action="{{ url_for('register') }}"`
      (removes the hardcoded URL)
    - add `value="{{ name or '' }}"` / `value="{{ email or '' }}"` so the
      fields keep their values after a validation error
    - add `minlength="8"` to the password input
  - `templates/login.html` — render flashed messages
    (`get_flashed_messages(with_categories=true)`) above the form, so the
    "Account created" message appears after the redirect

## Files to change
- `app.py` — set `SECRET_KEY` (needed for `flash`), merge GET/POST into the
  `register()` view, add validation, call the DB helpers, `flash` + `redirect`
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — see Templates
- `templates/login.html` — see Templates
- `static/css/style.css` — add an `.auth-success` style next to the existing
  `.auth-error` (around line 413), using only CSS variables (`--accent`,
  `--accent-light`, `--radius-sm`)
- `CLAUDE.md` — update the routes table to mark `POST /register` as
  implemented

## Files to create
- `tests/conftest.py` — pytest fixtures: Flask test `client` pointed at a
  temporary SQLite file (monkeypatch `database.db.DB_PATH`, then call
  `init_db()`)
- `tests/test_registration.py` — tests for the cases listed under Definition
  of done

## New dependencies
No new dependencies. `flask`, `werkzeug`, `pytest` and `pytest-flask` are
already in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs. Use raw `sqlite3` through `get_db()` only
- Parameterised queries only (`?` placeholders). Never use f-strings or
  `%`/`.format` in SQL
- Hash passwords with werkzeug (`generate_password_hash`). Never store or log
  the plain-text password
- Use CSS variables. Never hardcode hex values
- All templates extend `base.html`
- All DB access goes in `database/db.py`. The route never calls
  `conn.execute` directly
- Use `url_for()` for every internal link, form action and redirect
- Normalise input before validating: `strip()` the name and email, and
  `lower()` the email
- Validation rules, checked in this order and reporting the first failure:
  1. all four fields (name, email, password, confirm password) are present
     and non-empty after stripping → "All fields are required."
  2. the email contains `@` and has a `.` after it → "Please enter a valid
     email address."
  3. the password is at least 8 characters → "Password must be at least 8
     characters."
  4. the password and confirm password match → "Passwords do not match."
  5. the email is not already registered → "An account with this email
     already exists."
- Also catch `sqlite3.IntegrityError` from `create_user` (two simultaneous
  submits with the same email) and show the duplicate-email message. Do not
  let it surface as a 500
- `SECRET_KEY`: `os.environ.get("SECRET_KEY", "dev-secret-change-me")`. Do not
  commit a real secret
- Do not create a session or log the user in. That is Step 3
- Do not implement any other stub routes (`/logout`, `/profile`, `/expenses/*`)
- Keep port 5001

## Definition of done
- [ ] `python app.py` starts on port 5001 without errors
- [ ] `GET /register` still renders the form (200)
- [ ] Submitting valid details (new email, 8+ character password) redirects to
      `/login`, and the login page shows a success message
- [ ] The new row exists in `users`, and `password_hash` is a werkzeug hash,
      not the plain password
- [ ] The email is stored lowercase and trimmed (`  Foo@Bar.com ` →
      `foo@bar.com`)
- [ ] Registering `demo@spendly.com` (or any existing email, in any letter
      case) re-renders the form with "An account with this email already
      exists." and status 400. No new row is inserted
- [ ] A blank name, email, password or confirm password shows "All fields
      are required." and status 400
- [ ] Mismatched password and confirm password show "Passwords do not
      match." and status 400. No row is inserted
- [ ] An invalid email (e.g. `foo`) shows the invalid-email error and status
      400
- [ ] A password under 8 characters shows the password-length error and
      status 400
- [ ] After a validation error, the name and email fields keep their values,
      and the password field is empty
- [ ] `register.html` has no hardcoded `/register` URL
- [ ] No hex colour values were added to CSS
- [ ] `pytest` passes, including `tests/test_registration.py`
