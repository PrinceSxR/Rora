# Spec: Profile Page Design

## Overview
Replace the `GET /profile` stub with a real, styled profile page for the
signed-in user. Login (Step 3) already redirects to `/profile`, so this is the
first page a user sees after signing in. This step sets the page layout that
later steps fill with live data. The page has four parts: a user card (avatar
initials, name, email, member-since month), a row of three summary stats
(total spent, number of transactions, top category), a recent-transactions
table, and a spending-by-category breakdown. The user card reads the real user
from the database. The stats, transactions and categories use **hardcoded
placeholder data** defined in `app.py`. Querying real expenses is out of scope
here; later steps replace the placeholders. Anyone who is not signed in is sent
to the login page.

## Depends on
- **Step 1 — Database setup** (complete): `users` table with `created_at`, and
  `get_db()`.
- **Step 2 — Registration** (complete, on `master`).
- **Step 3 — Login and logout** (**not yet on `master`**). It exists in commit
  `771b5d0` on `feature/login-logout`. This step needs `session["user_id"]`,
  `session["user_name"]`, the `/logout` route and the signed-in navbar in
  `base.html` from it. Merge Step 3 into `master` (and into this branch) before
  implementing.

## Routes
- `GET /profile` — render `profile.html` for the signed-in user — logged-in.
  If `session["user_id"]` is missing, or no longer matches a row in `users`,
  call `session.clear()`, flash "Please sign in to view your profile." (category
  `error`), and redirect to `url_for('login')`. Flash *after* clearing, because
  `clear()` also wipes pending flashes.

No other new routes.

## Database changes
No database changes. The existing `users` table already has `id`, `name`,
`email` and `created_at`.

New helper in `database/db.py` (no schema change):
- `get_user_by_id(user_id)` — `SELECT id, name, email, created_at FROM users
  WHERE id = ?`. Returns the `sqlite3.Row` or `None`. Do not select
  `password_hash`, because the profile never needs it.

## Templates
- **Create:**
  - `templates/profile.html` — extends `base.html`. Loads `css/profile.css` in
    the `head` block (add one to `base.html` if it does not already exist).
    Sections:
    1. **User card** — a circle avatar with the initials, the name as the
       heading, the email, and "Member since <Month YYYY>" (omit the line if
       the date is missing).
    2. **Stats row** — three cards: Total spent (`₹` with comma separators and
       2 decimals), Transactions (an integer), and Top category.
    3. **Recent transactions** — a table with Date, Description, Category (as a
       pill/badge) and Amount (right-aligned, `₹`, 2 decimals), newest first.
       Show an empty-state message if the list is empty.
    4. **Spending by category** — one row per category: the name, the amount,
       the percent, and a horizontal bar whose width is set from the percent.
       Ordered largest first. Show an empty-state message if the list is empty.
- **Modify:**
  - `templates/base.html` — add a `{% block head %}{% endblock %}` inside
    `<head>` after `style.css` (if it is missing), and a "Profile" link to
    `url_for('profile')` in the signed-in navbar.

## Files to change
- `app.py` — import `get_user_by_id`; add the `_initials(name)` and
  `_member_since(created_at)` helpers; add a `PLACEHOLDER_PROFILE_DATA` constant
  (`stats`, `transactions`, `categories`); replace the `profile()` stub
- `database/db.py` — add `get_user_by_id()`
- `templates/base.html` — see Templates
- `CLAUDE.md` — add `profile.css` to the architecture tree; mark `GET /profile`
  as implemented (Step 4: login required, user card from DB, placeholder
  stats/transactions/categories); add `get_user_by_id()` to the list of
  db.py helpers

## Files to create
- `templates/profile.html`
- `static/css/profile.css` — profile-page-only styles
- `tests/test_profile.py` — tests for the cases listed under Definition of done

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs. Use raw `sqlite3` through `get_db()` only
- Parameterised queries only (`?` placeholders). Never use f-strings in SQL
- Passwords hashed with werkzeug. This step never reads or exposes
  `password_hash`
- Use CSS variables from `style.css` (`--ink*`, `--paper*`, `--accent*`,
  `--danger*`, `--border*`, `--radius-*`, `--font-*`). Never hardcode hex
  values
- All templates extend `base.html`
- Page-specific styles go in `static/css/profile.css`. No inline `<style>`
  tags. The only inline style allowed is the category bar's width
  (`style="width: {{ c.percent }}%"`)
- `url_for()` for every internal link and redirect
- DB access only in `database/db.py`. The route fetches the data, renders the
  template, and does nothing else
- `_initials`: "Demo User" → "DU", a single word → its first letter,
  blank → "?". Always uppercase
- `_member_since`: `"2026-10-10 12:34:56"` → `"October 2026"`. Return `None`
  for a missing or malformed value. Never raise
- Placeholder data stays internally consistent: category amounts sum to
  `total_spent`, the percents roughly sum to 100, and `transaction_count`
  equals the number of transactions
- Layout must work at phone width: the stats row and the two lower sections
  stack into a single column on narrow screens, and the page has no horizontal
  scroll
- Jinja autoescaping stays on. Do not use `|safe` on user data
- Do not query the `expenses` table, and do not implement any other stub
  routes (`/expenses/*`)
- Keep port 5001

## Definition of done
- [ ] `python app.py` starts on port 5001 without errors
- [ ] Visiting `/profile` while signed out redirects to `/login` and shows
      "Please sign in to view your profile."
- [ ] Signing in as `demo@spendly.com` / `demo123` lands on `/profile` (200)
- [ ] The user card shows "DU", "Demo User", "demo@spendly.com" and
      "Member since <current month and year>"
- [ ] The stats row shows the placeholder total (`₹` with 2 decimals), the
      transaction count, and the top category
- [ ] The recent-transactions table lists the placeholder rows, newest first,
      with right-aligned `₹` amounts and category badges
- [ ] The category breakdown shows bars whose widths match their percents,
      largest first
- [ ] A newly registered user sees their own name, email and initials
- [ ] A session whose `user_id` no longer exists in `users` is cleared and
      redirected to `/login`
- [ ] The navbar shows a "Profile" link while signed in. "Sign out" still
      works and `/profile` is then blocked again
- [ ] At about 375px width, the page stacks into one column with no horizontal
      scroll
- [ ] No hex colour values were added to CSS, and no `<style>` tags or
      hardcoded internal URLs were added to templates
- [ ] `pytest` passes, including `tests/test_profile.py`
