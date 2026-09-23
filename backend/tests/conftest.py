"""Shared pytest fixtures.

Tests run against a SEPARATE database (ticketing_test), so your dev data is never touched.
"""

import os
from pathlib import Path

# Must be set BEFORE importing the app, because settings are read at import time
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://ticketing:ticketing@localhost:5432/ticketing_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _create_database_if_missing(url: str) -> None:
    db_url = make_url(url)
    admin_engine = create_engine(db_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_url.database},
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Create the test DB once and run all migrations (down, then up)."""
    _create_database_if_missing(TEST_DATABASE_URL)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.downgrade(config, "base")  # also proves downgrade() works
    command.upgrade(config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    """Every test starts with an empty table."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE tickets RESTART IDENTITY"))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
