import os

from flask import Flask, flash, redirect, render_template, request, url_for

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DUPLICATE_EMAIL_ERROR = "An account with this email already exists."

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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
