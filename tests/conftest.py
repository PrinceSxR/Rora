import os
import tempfile

import pytest

import database.db as db

# app.py runs init_db()/seed_db() at import time, so point it at a throwaway
# file before importing it — tests must never touch expense_tracker.db.
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "import.db")

from app import app as flask_app  # noqa: E402


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    flask_app.config.update(TESTING=True)
    yield flask_app


@pytest.fixture
def user_count(app):
    def count():
        conn = db.get_db()
        try:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        finally:
            conn.close()

    return count
