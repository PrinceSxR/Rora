import pytest

import app as app_module
import database.db as db
from app import _format_inr, _initials, _member_since

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
LOGIN_MSG = b"Please sign in to view your profile."


def login(client, email=DEMO_EMAIL, password=DEMO_PASSWORD, follow_redirects=False):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=follow_redirects,
    )


def register(client, name, email, password="password123"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )


def profile_page(client):
    login(client)
    response = client.get("/profile")
    assert response.status_code == 200
    return response.data


# ------------------------------------------------------------------ #
# Access control                                                      #
# ------------------------------------------------------------------ #

def test_profile_signed_out_redirects_to_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_profile_signed_out_flashes_message(client):
    response = client.get("/profile", follow_redirects=True)
    assert response.request.path == "/login"
    assert LOGIN_MSG in response.data
    assert b"auth-error" in response.data


def test_stale_user_id_clears_session_and_redirects(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 9999
        sess["user_name"] = "Ghost"
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "user_name" not in sess


def test_profile_blocked_after_logout(client):
    login(client)
    assert client.get("/profile").status_code == 200
    client.get("/logout")
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


# ------------------------------------------------------------------ #
# User card                                                           #
# ------------------------------------------------------------------ #

def test_login_lands_on_profile_with_welcome(client):
    response = login(client, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/profile"
    assert b"Welcome back, Demo User!" in response.data


def test_profile_is_not_stub(client):
    assert b"coming in Step 4" not in profile_page(client)


def test_user_card_shows_demo_user(client):
    data = profile_page(client)
    demo = db.get_user_by_email(DEMO_EMAIL)
    since = _member_since(demo["created_at"])
    assert b'class="profile-avatar" aria-hidden="true">DU<' in data
    assert b"Demo User" in data
    assert DEMO_EMAIL.encode() in data
    assert f"Member since {since}".encode() in data


def test_new_user_sees_own_details(client):
    register(client, "Alice Smith", "alice@example.com")
    login(client, email="alice@example.com", password="password123")
    data = client.get("/profile").data
    assert b">AS<" in data
    assert b"Alice Smith" in data
    assert b"alice@example.com" in data
    assert b'class="profile-name">Demo User' not in data


def test_user_name_is_escaped(client):
    register(client, "<script>x</script>", "xss@example.com")
    login(client, email="xss@example.com", password="password123")
    data = client.get("/profile").data
    assert b"<script>x</script>" not in data
    assert b"&lt;script&gt;x&lt;/script&gt;" in data


# ------------------------------------------------------------------ #
# Placeholder content                                                 #
# ------------------------------------------------------------------ #

def test_stats_row(client):
    data = profile_page(client)
    assert "₹8,700.00".encode() in data
    assert b'class="stat-value">8<' in data
    assert b'class="stat-value">Shopping<' in data


def test_transactions_newest_first(client):
    data = profile_page(client)
    assert data.index(b"2026-10-09") < data.index(b"2026-09-30")
    assert b'class="cat-pill cat-food"' in data
    assert b'class="num"' in data
    assert "₹1,240.50".encode() in data


def test_category_bars_widths_and_order(client):
    data = profile_page(client)
    assert b'style="width: 33%"' in data
    assert b'style="width: 2%"' in data
    assert data.index(b'cat-row cat-shopping') < data.index(b'cat-row cat-other')


def test_empty_states(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "PLACEHOLDER_PROFILE_DATA",
        {
            "stats": {"total_spent": 0.0, "transaction_count": 0, "top_category": None},
            "transactions": [],
            "categories": [],
        },
    )
    data = profile_page(client)
    assert b"No transactions yet." in data
    assert b"No spending yet." in data
    assert b"txn-table" not in data


def test_placeholder_data_consistent():
    data = app_module.PLACEHOLDER_PROFILE_DATA
    stats, transactions, categories = (
        data["stats"], data["transactions"], data["categories"]
    )
    assert sum(c["amount"] for c in categories) == pytest.approx(stats["total_spent"])
    assert sum(t["amount"] for t in transactions) == pytest.approx(stats["total_spent"])
    assert abs(sum(c["percent"] for c in categories) - 100) <= 2
    assert stats["transaction_count"] == len(transactions)
    assert stats["top_category"] == categories[0]["name"]
    dates = [t["date"] for t in transactions]
    assert dates == sorted(dates, reverse=True)
    amounts = [c["amount"] for c in categories]
    assert amounts == sorted(amounts, reverse=True)


# ------------------------------------------------------------------ #
# Navbar                                                              #
# ------------------------------------------------------------------ #

def test_navbar_has_profile_link_when_signed_in(client):
    data = profile_page(client)
    assert b'href="/profile" class="nav-user"' in data
    assert b"Sign out" in data


def test_navbar_no_profile_link_when_signed_out(client):
    assert b'href="/profile"' not in client.get("/terms").data


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize(
    "name, expected",
    [
        ("Demo User", "DU"),
        ("alice", "A"),
        ("mary jane watson", "MW"),
        ("   ", "?"),
    ],
)
def test_initials(name, expected):
    assert _initials(name) == expected


@pytest.mark.parametrize(
    "created_at, expected",
    [
        ("2026-10-10 12:34:56", "October 2026"),
        ("2025-01-01", "January 2025"),
        (None, None),
        ("", None),
        ("garbage", None),
    ],
)
def test_member_since(created_at, expected):
    assert _member_since(created_at) == expected


def test_format_inr():
    assert _format_inr(1234567.5) == "₹1,234,567.50"
    assert _format_inr(0) == "₹0.00"


# ------------------------------------------------------------------ #
# DB helper                                                           #
# ------------------------------------------------------------------ #

def test_get_user_by_id(app):
    demo = db.get_user_by_email(DEMO_EMAIL)
    user = db.get_user_by_id(demo["id"])
    assert user["email"] == DEMO_EMAIL
    assert "password_hash" not in user.keys()
    assert db.get_user_by_id(9999) is None
