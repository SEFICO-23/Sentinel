"""Tests for the database persistence layer."""
import pytest
from data_loader import load_commitment_tracker, load_executed_calls
import database as db


class TestDatabaseInit:
    def test_tables_created(self):
        with db.get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = [t[0] for t in tables]
        assert "commitment_tracker" in table_names
        assert "executed_calls" in table_names
        assert "processed_calls" in table_names
        assert "users" in table_names

    def test_default_users_seeded(self):
        users = db.get_users()
        assert len(users) == 5
        usernames = [u["username"] for u in users]
        assert "s.mueller" in usernames
        assert "a.schmidt" in usernames


class TestSeedFromExcel:
    def test_commitment_tracker_seeded(self):
        ct = load_commitment_tracker()
        db.seed_from_excel(ct, load_executed_calls())
        rows = db.get_commitment_tracker()
        assert len(rows) == 12  # 12 funds

    def test_idempotent_seed(self):
        """Seeding twice should not duplicate data."""
        ct = load_commitment_tracker()
        ex = load_executed_calls()
        db.seed_from_excel(ct, ex)
        db.seed_from_excel(ct, ex)
        rows = db.get_commitment_tracker()
        assert len(rows) == 12


class TestUserRoles:
    def test_reviewers_are_reviewer_or_admin(self):
        reviewers = db.get_reviewers()
        for r in reviewers:
            assert r["role"] in ("reviewer", "admin")

    def test_reviewers_count(self):
        reviewers = db.get_reviewers()
        assert len(reviewers) == 3  # 2 reviewers + 1 admin


class TestCapitalCallExecution:
    @pytest.fixture(autouse=True)
    def seed_data(self):
        db.seed_from_excel(load_commitment_tracker(), load_executed_calls())

    def test_execute_updates_commitment(self):
        # Get initial state
        fund = db.get_commitment_for_fund("GT Partners V Equity")
        initial_remaining = fund["remaining_open_commitment"]

        validation = {
            "fund_name_matched": "GT Partners V Equity",
            "fund_name_extracted": "GT Partners V Equity",
            "fund_match_score": 100.0,
            "amount": 1_000_000,
            "currency": "EUR",
            "due_date": "16.03.2026",
            "investor": "C - Fund Vintage 2015",
            "commitment_check": {"passed": True, "message": "OK"},
            "wire_check": {"passed": True, "message": "OK"},
            "overall_status": "APPROVED",
        }

        db.execute_capital_call(validation, "a.schmidt", "Test", "test.pdf", "<email>")

        # Verify commitment was reduced
        fund_after = db.get_commitment_for_fund("GT Partners V Equity")
        assert fund_after["remaining_open_commitment"] == initial_remaining - 1_000_000

    def test_execute_creates_audit_record(self):
        validation = {
            "fund_name_matched": "GT Partners V Equity",
            "fund_name_extracted": "GT Partners V Equity",
            "fund_match_score": 100.0,
            "amount": 500_000,
            "currency": "EUR",
            "due_date": "16.03.2026",
            "investor": "C - Fund Vintage 2015",
            "commitment_check": {"passed": True, "message": "OK"},
            "wire_check": {"passed": True, "message": "OK"},
            "overall_status": "APPROVED",
        }

        db.execute_capital_call(validation, "a.schmidt", "Test", "audit_test.pdf", "<email>")
        processed = db.get_processed_calls()
        assert len(processed) >= 1
        assert processed[0]["action"] == "EXECUTED"
        assert processed[0]["filename"] == "audit_test.pdf"

    def test_duplicate_detection(self):
        validation = {
            "fund_name_matched": "GT Partners V Equity",
            "fund_name_extracted": "GT Partners V Equity",
            "fund_match_score": 100.0,
            "amount": 2_000_000,
            "currency": "EUR",
            "due_date": "16.03.2026",
            "investor": "C - Fund Vintage 2015",
            "commitment_check": {"passed": True, "message": "OK"},
            "wire_check": {"passed": True, "message": "OK"},
            "overall_status": "APPROVED",
        }

        db.execute_capital_call(validation, "a.schmidt", "", "dupe.pdf", "<email>")
        assert db.is_file_already_processed("dupe.pdf") is True
        assert db.is_file_already_processed("other.pdf") is False


class TestRejectionLogging:
    def test_rejection_creates_record(self):
        validation = {
            "fund_name_matched": "GT Partners IV Equity",
            "fund_name_extracted": "GT Partners IV Equity",
            "fund_match_score": 100.0,
            "amount": 5_600_000,
            "currency": "EUR",
            "due_date": "16.03.2026",
            "investor": "C - Fund Vintage 2010",
            "commitment_check": {"passed": False, "message": "Over commitment"},
            "wire_check": {"passed": True, "message": "OK"},
            "overall_status": "REJECTED - OVER COMMITMENT",
        }

        db.log_rejection(validation, "m.weber", "Too much", "rejected.pdf")
        processed = db.get_processed_calls()
        assert any(p["action"] == "REJECTED" for p in processed)
