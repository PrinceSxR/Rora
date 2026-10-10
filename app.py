import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DUPLICATE_EMAIL_ERROR = "An account with this email already exists."
LOGIN_REQUIRED_ERROR = "Email and password are required."
INVALID_LOGIN_ERROR = "Invalid email or password."
PROFILE_LOGIN_REQUIRED = "Please sign in to view your profile."

# TEMPORARY placeholder data for the Step 4 profile design.
# A later step replaces this with real expense queries — keep the same
# keys and shapes so profile.html does not need to change.
PLACEHOLDER_PROFILE_DATA = {
    "stats": {
        "total_spent": 8700.00,
        "transaction_count": 8,
        "top_category": "Shopping",
    },
    "transactions": [  # newest first
        {"date": "2026-10-09", "description": "Groceries",
         "category": "Food", "amount": 1240.50},
        {"date": "2026-10-08", "description": "Electricity bill",
         "category": "Bills", "amount": 2150.00},
        {"date": "2026-10-06", "description": "Metro card recharge",
         "category": "Transport", "amount": 500.00},
        {"date": "2026-10-05", "description": "Pharmacy",
         "category": "Health", "amount": 385.75},
        {"date": "2026-10-03", "description": "Movie tickets",
         "category": "Entertainment", "amount": 640.00},
        {"date": "2026-10-02", "description": "Running shoes",
         "category": "Shopping", "amount": 2899.00},
        {"date": "2026-10-01", "description": "Lunch with team",
         "category": "Food", "amount": 720.00},
        {"date": "2026-09-30", "description": "Stationery",
         "category": "Other", "amount": 164.75},
    ],
    "categories": [  # largest first; percent = round(amount / total * 100)
        {"name": "Shopping", "amount": 2899.00, "percent": 33},
        {"name": "Bills", "amount": 2150.00, "percent": 25},
        {"name": "Food", "amount": 1960.50, "percent": 23},
        {"name": "Entertainment", "amount": 640.00, "percent": 7},
        {"name": "Transport", "amount": 500.00, "percent": 6},
        {"name": "Health", "amount": 385.75, "percent": 4},
        {"name": "Other", "amount": 164.75, "percent": 2},
    ],
}

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _validate_registration(name, email, password, confirm_password):
    """Return the first validation error message, or None if valid."""
    if not name or not email or not password or not confirm_password:
        return "All fields are required."
    local, _, domain = email.partition("@")
    if not local or "." not in domain:
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if password != confirm_password:
        return "Passwords do not match."
    if get_user_by_email(email) is not None:
        return DUPLICATE_EMAIL_ERROR
    return None


def _initials(name):
    """'Demo User' -> 'DU'; single word -> first letter; blank -> '?'."""
    parts = name.split()
    if not parts:
        return "?"
    letters = parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")
    return letters.upper()


def _member_since(created_at):
    """'2026-10-10 12:34:56' -> 'October 2026'; None if missing or malformed."""
    try:
        return datetime.strptime(created_at[:10], "%Y-%m-%d").strftime("%B %Y")
    except (TypeError, ValueError):
        return None


@app.template_filter("inr")
def _format_inr(amount):
    return f"₹{amount:,.2f}"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    error = _validate_registration(name, email, password, confirm_password)
    if error is None and create_user(name, email, password) is None:
        error = DUPLICATE_EMAIL_ERROR
    if error:
        return render_template(
            "register.html", error=error, name=name, email=email
        ), 400

    flash("Account created! Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html", error=LOGIN_REQUIRED_ERROR, email=email
        ), 400

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", error=INVALID_LOGIN_ERROR, email=email
        ), 401

    # Clear first to prevent session fixation; flash after, since flashes
    # live in the session and would otherwise be wiped.
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    flash(f"Welcome back, {user['name']}!", "success")
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    user = get_user_by_id(user_id) if user_id is not None else None
    if user is None:
        # Also drops a stale user_id; flash after, since clear() wipes flashes.
        session.clear()
        flash(PROFILE_LOGIN_REQUIRED, "error")
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        user={
            "name": user["name"],
            "email": user["email"],
            "initials": _initials(user["name"]),
            "member_since": _member_since(user["created_at"]),
        },
        **PLACEHOLDER_PROFILE_DATA,
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
