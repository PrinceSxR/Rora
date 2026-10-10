import pytest

import database.db as db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
INVALID_MSG = b"Invalid email or password."
REQUIRED_MSG = b"Email and password are required."


def login(client, email=DEMO_EMAIL, password=DEMO_PASSWORD, follow_redirects=False):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=follow_redirects,
    )


# ------------------------------------------------------------------ #
# Login — happy path                                                  #
# ------------------------------------------------------------------ #

def test_get_login_renders_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b'name="email"' in response.data


def test_valid_login_redirects_to_profile(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_valid_login_sets_session(client):
    login(client)
    demo = db.get_user_by_email(DEMO_EMAIL)
    with client.session_transaction() as sess:
        assert sess["user_id"] == demo["id"]
        assert sess["user_name"] == "Demo User"


def test_login_email_case_and_whitespace_insensitive(client):
    response = login(client, email="  DEMO@Spendly.com ")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_newly_registered_user_can_log_in(client):
    client.post(
        "/register",
        data={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    response = login(client, email="alice@example.com", password="password123")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    with client.session_transaction() as sess:
        assert sess["user_name"] == "Alice Smith"


def test_login_clears_preexisting_session(client):
    with client.session_transaction() as sess:
        sess["foo"] = "bar"
    login(client)
    with client.session_transaction() as sess:
        assert "foo" not in sess
        assert "user_id" in sess


# ------------------------------------------------------------------ #
# Login — failures                                                    #
# ------------------------------------------------------------------ #

def test_wrong_password_rejected(client):
    response = login(client, password="wrong-password")
    assert response.status_code == 401
    assert INVALID_MSG in response.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_unknown_email_rejected_with_same_message(client):
    response = login(client, email="nobody@example.com")
    assert response.status_code == 401
    assert INVALID_MSG in response.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


@pytest.mark.parametrize(
    "email, password",
    [("", DEMO_PASSWORD), (DEMO_EMAIL, ""), ("   ", DEMO_PASSWORD)],
)
def test_blank_email_or_password(client, email, password):
    response = login(client, email=email, password=password)
    assert response.status_code == 400
    assert REQUIRED_MSG in response.data


def test_failed_login_keeps_email_not_password(client):
    response = login(client, password="secret-guess")
    assert response.status_code == 401
    assert f'value="{DEMO_EMAIL}"'.encode() in response.data
    assert b"secret-guess" not in response.data


# ------------------------------------------------------------------ #
# Navbar                                                              #
# ------------------------------------------------------------------ #

def test_navbar_signed_in(client):
    login(client)
    response = client.get("/terms")
    assert b"Demo User" in response.data
    assert b'href="/logout"' in response.data
    assert b"Sign out" in response.data
    assert b"Get started" not in response.data
    assert b">Sign in<" not in response.data


def test_navbar_signed_out(client):
    response = client.get("/terms")
    assert b"Get started" in response.data
    assert b">Sign in<" in response.data
    assert b"Sign out" not in response.data


# ------------------------------------------------------------------ #
# Logout                                                              #
# ------------------------------------------------------------------ #

def test_logout_clears_session_and_redirects(client):
    login(client)
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "user_name" not in sess


def test_logout_shows_signed_out_message(client):
    login(client)
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/login"
    assert b"You have been signed out." in response.data
    assert b"auth-success" in response.data
    assert b"Welcome back, Demo User" not in response.data


def test_logout_when_signed_out_is_safe(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_logout_is_not_stub(client):
    response = client.get("/logout", follow_redirects=True)
    assert b"coming in Step 3" not in response.data
