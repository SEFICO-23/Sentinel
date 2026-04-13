"""Shared test fixtures for Project Sentinel."""
import os
import sys
import pytest

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Use a separate test database
TEST_DB = os.path.join(PROJECT_ROOT, "test_sentinel.db")


@pytest.fixture(autouse=True)
def test_db(monkeypatch):
    """Use a temporary database for each test session."""
    import database as db
    monkeypatch.setattr(db, "DB_PATH", TEST_DB)
    db.init_db()
    db.seed_default_users()
    yield
    # Cleanup
    if os.path.exists(TEST_DB):
        os.unlink(TEST_DB)
    # WAL and SHM files
    for suffix in ["-wal", "-shm"]:
        path = TEST_DB + suffix
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def sample_notices_dir():
    """Return path to the project root where sample PDFs live."""
    return PROJECT_ROOT


@pytest.fixture
def test_notices_dir():
    """Return path to the test_notices directory."""
    return os.path.join(PROJECT_ROOT, "test_notices")
