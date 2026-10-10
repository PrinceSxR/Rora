import pytest
from werkzeug.security import check_password_hash

import database.db as db

VALID = {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "password": "password123",
    "confirm_password": "password123",
}
DUPLICATE_MSG = b"An account with this email already exists."


def post_register(client, follow_redirects=False, **overrides):
    return client.post(
        "/register", data={**VALID, **overrides}, follow_redirects=follow_redirects
    )


# ------------------------------------------------------------------ #
# Happy path                                                          #
# ------------------------------------------------------------------ #

def test_get_register_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'name="email"' in response.data
    assert b'action="/register"' in response.data


def test_valid_registration_redirects_to_login(client):
    response = post_register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_success_message_shown_on_login(client):
    response = post_register(client, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/login"
    assert b"auth-success" in response.data
    assert b"Account created" in response.data


def test_user_row_created_with_hashed_password(client):
    post_register(client)
    user = db.get_user_by_email("alice@example.com")
    assert user is not None
    assert user["name"] == "Alice Smith"
    assert user["password_hash"] != VALID["password"]
    assert check_password_hash(user["password_hash"], VALID["password"])


def test_email_and_name_normalised(client):
    post_register(client, name="  Bob  ", email="  Foo@Bar.com ")
    user = db.get_user_by_email("foo@bar.com")
    assert user is not None
    assert user["name"] == "Bob"


# ------------------------------------------------------------------ #
# Validation errors                                                   #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("email", ["demo@spendly.com", "DEMO@Spendly.COM"])
def test_duplicate_email_rejected(client, user_count, email):
    before = user_count()
    response = post_register(client, email=email)
    assert response.status_code == 400
    assert DUPLICATE_MSG in response.data
    assert user_count() == before


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"email": ""},
        {"password": ""},
        {"confirm_password": ""},
        {"name": "   "},
    ],
)
def test_blank_fields_rejected(client, user_count, overrides):
    before = user_count()
    response = post_register(client, **overrides)
    assert response.status_code == 400
    assert b"All fields are required." in response.data
    assert user_count() == before


@pytest.mark.parametrize("email", ["foo", "foo@bar", "@bar.com"])
def test_invalid_email_rejected(client, email):
    response = post_register(client, email=email)
    assert response.status_code == 400
    assert b"Please enter a valid email address." in response.data


def test_short_password_rejected(client, user_count):
    before = user_count()
    response = post_register(client, password="short1")
    assert response.status_code == 400
    assert b"Password must be at least 8 characters." in response.data
    assert user_count() == before


def test_mismatched_passwords_rejected(client, user_count):
    before = user_count()
    response = post_register(client, confirm_password="password124")
    assert response.status_code == 400
    assert b"Passwords do not match." in response.data
    assert user_count() == before


def test_validation_order(client):
    response = post_register(client, name="", email="foo")
    assert b"All fields are required." in response.data
    response = post_register(client, email="foo", password="short")
    assert b"Please enter a valid email address." in response.data
    response = post_register(client, password="short", confirm_password="other")
    assert b"Password must be at least 8 characters." in response.data


def test_fields_retained_password_cleared(client):
    response = post_register(client, email="Alice@Example.com", password="tiny")
    assert response.status_code == 400
    assert b'value="Alice Smith"' in response.data
    assert b'value="alice@example.com"' in response.data
    assert b"tiny" not in response.data


def test_integrity_error_race_shows_duplicate(client, user_count, monkeypatch):
    # Simulate a concurrent insert: the pre-check misses the existing row.
    monkeypatch.setattr("app.get_user_by_email", lambda email: None)
    before = user_count()
    response = post_register(client, email="demo@spendly.com")
    assert response.status_code == 400
    assert DUPLICATE_MSG in response.data
    assert user_count() == before


# ------------------------------------------------------------------ #
# DB helpers                                                          #
# ------------------------------------------------------------------ #

def test_create_user_returns_none_on_duplicate(app):
    user_id = db.create_user("Carol", "carol@example.com", "password123")
    assert isinstance(user_id, int)
    assert db.create_user("Carol", "carol@example.com", "password123") is None


def test_get_user_by_email_missing_returns_none(app):
    assert db.get_user_by_email("nobody@example.com") is None
