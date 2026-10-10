# Spec: Login and Logout

## Overview
Make the existing sign-in form work and let users sign out. Right now
`GET /login` renders `login.html`, but the form posts to `/login` and no route
accepts `POST`. `GET /logout` is still a raw-string stub. This step adds
session-based authentication. `POST /login` looks up the user by email and
checks the password with werkzeug's `check_password_hash`. On success it
stores the user's id and name in Flask's signed-cookie `session`. `GET /logout`
clears the session. The navbar also changes to show the signed-in state. This
is the first step that knows who the current user is. Step 4 (profile) and
every expense step after it (7–9) rely on `session["user_id"]`.

## Depends on
- **Step 1 — Database setup** (complete): `users` table, `get_db()`, seeded
  demo user `demo@spendly.com` / `demo123`.
- **Step 2 — Registration** (complete): `get_user_by_email()`,
  `SECRET_KEY` config, flash rendering in `login.html`, `.auth-success` /
  `.auth-error` styles, `tests/conftest.py` fixtures.

## Routes
- `GET /login` — render the sign-in form — public (already exists; merged
  into one view with POST)
- `POST /login` — validate credentials. On success: clear and populate the
  session, flash a welcome message, redirect to `url_for('profile')`. On
  failure: re-render `login.html` with an error and the entered email, HTTP
  status 401 — public
- `GET /logout` — clear the session, flash "You have been signed out.",
  redirect to `url_for('login')` — public (safe to hit when already signed
  out)

Use one view function: `@app.route("/login", methods=["GET", "POST"])`.
Keep `/logout` as `GET` to match the existing roadmap route and navbar link.

## Database changes
No database changes. The existing `users` table and `get_user_by_email()`
cover login. No new DB helpers are needed. Password checking is not DB logic,
so `check_password_hash` is called from `app.py`.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html`
    - add `value="{{ email or '' }}"` to the email input so it keeps its
      value after a failed login (the password field stays empty)
  - `templates/base.html` — make the navbar `.nav-links` session-aware:
    - signed out (no `session.user_id`): keep the current "Sign in" and
      "Get started" links
    - signed in: show the user's name (`session.user_name`) and a
      "Sign out" link to `url_for('logout')` with class `nav-cta`, so it
      stays visible on mobile (the mobile rule hides non-`nav-cta` links)

## Files to change
- `app.py`
  - import `session` from flask and `check_password_hash` from
    `werkzeug.security`
  - merge GET/POST into `login()`. Normalise the email (`strip().lower()`)
    and check credentials
  - replace the `logout()` stub with a real implementation
- `templates/login.html` — see Templates
- `templates/base.html` — see Templates
- `static/css/style.css` — only if needed for the navbar user-name label
  (e.g. `.nav-user`). Use CSS variables only (`--ink-muted` etc.)
- `CLAUDE.md` — mark `POST /login` and `GET /logout` as implemented (Step 3)
  in the routes table

## Files to create
- `tests/test_auth.py` — tests for the cases listed under Definition of done
  (reuse the existing `app` fixture in `tests/conftest.py`)

## New dependencies
No new dependencies. Flask's built-in `session` and werkzeug's
`check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs. Use raw `sqlite3` through `get_db()` only
- Parameterised queries only (`?` placeholders)
- Passwords are checked with werkzeug's `check_password_hash`. Never compare
  plain text, and never log or flash the password
- Use CSS variables. Never hardcode hex values
- All templates extend `base.html`
- All DB access goes in `database/db.py`. The route never calls
  `conn.execute` directly
- Use `url_for()` for every internal link, form action and redirect
- Validation order for `POST /login`:
  1. email or password empty after stripping the email → "Email and
     password are required." (status 400)
  2. no user with that email, **or** the password does not match → the
     same generic message "Invalid email or password." (status 401). Never
     reveal which part was wrong
- On successful login call `session.clear()` before setting
  `session["user_id"]` and `session["user_name"]`. This prevents session
  fixation
- `logout()` calls `session.clear()`. It must not error when no one is
  signed in
- Do not add a `login_required` decorator or protect any routes yet. That
  starts in Step 4
- Do not implement any other stub routes (`/profile`, `/expenses/*`).
  Redirecting to `url_for('profile')` after login is fine even though it is
  still a stub
- Do not change `SECRET_KEY` handling or the port (5001)

## Definition of done
- [ ] `python app.py` starts on port 5001 without errors
- [ ] `GET /login` still renders the form (200)
- [ ] Logging in as `demo@spendly.com` / `demo123` redirects to `/profile`
      and sets `user_id` and `user_name` in the session
- [ ] Email matching ignores case and whitespace (`  DEMO@Spendly.com `
      logs in)
- [ ] A wrong password shows "Invalid email or password." with status 401.
      No session is set
- [ ] An unknown email shows the same "Invalid email or password." message
      and status 401
- [ ] A blank email or password shows "Email and password are required."
      with status 400
- [ ] After a failed login, the email field keeps its value and the password
      field is empty
- [ ] A user who has just registered (Step 2 flow) can log in with their new
      credentials
- [ ] While signed in, the navbar shows the user's name and a "Sign out"
      link, and hides "Sign in" / "Get started"
- [ ] `GET /logout` clears the session, redirects to `/login`, and the login
      page shows "You have been signed out."
- [ ] `GET /logout` while signed out still redirects to `/login` without
      error
- [ ] `/logout` no longer returns the raw "coming in Step 3" string
- [ ] No hex colour values were added to CSS
- [ ] `pytest` passes, including `tests/test_auth.py` and the existing
      `tests/test_registration.py`
