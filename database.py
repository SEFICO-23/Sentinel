"""
SQLite persistence layer for Project Sentinel.
Replaces in-memory session state with durable storage.
"""
import sqlite3
import os
import json
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "sentinel.db")

# ─── PDF Archive ───

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive", "capital_calls")


def archive_pdf(file_bytes: bytes, filename: str) -> str:
    """Save PDF to archive. Returns the archive path."""
    now = datetime.now()
    dir_path = os.path.join(ARCHIVE_DIR, str(now.year), f"{now.month:02d}")
    os.makedirs(dir_path, exist_ok=True)

    # Add timestamp to avoid collisions
    safe_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = os.path.join(dir_path, safe_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return file_path


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS commitment_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor TEXT NOT NULL,
            fund_name TEXT NOT NULL UNIQUE,
            total_commitment REAL NOT NULL,
            total_funded_ytd REAL NOT NULL DEFAULT 0,
            remaining_open_commitment REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS executed_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor TEXT NOT NULL,
            fund_name TEXT NOT NULL,
            amount REAL NOT NULL,
            value_date TEXT NOT NULL,
            source TEXT DEFAULT 'historical',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS processed_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            fund_name_extracted TEXT,
            fund_name_matched TEXT,
            fund_match_score REAL,
            investor TEXT,
            amount REAL,
            currency TEXT DEFAULT 'EUR',
            due_date TEXT,
            iban_extracted TEXT,
            iban_approved TEXT,
            commitment_passed INTEGER,
            commitment_message TEXT,
            wire_passed INTEGER,
            wire_message TEXT,
            overall_status TEXT NOT NULL,
            action TEXT NOT NULL,
            reviewer TEXT,
            review_notes TEXT,
            email_body TEXT,
            email_sent INTEGER NOT NULL DEFAULT 0,
            email_recipient TEXT,
            validation_json TEXT,
            processed_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS commitment_amendments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            current_commitment REAL NOT NULL,
            current_remaining REAL NOT NULL,
            requested_increase REAL NOT NULL,
            new_commitment REAL NOT NULL,
            reason TEXT NOT NULL,
            capital_call_filename TEXT,
            requested_by TEXT NOT NULL,
            reviewed_by TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
            review_notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            reviewed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('analyst', 'reviewer', 'admin')),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS approved_wires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            beneficiary_bank TEXT NOT NULL,
            swift_bic TEXT,
            iban TEXT NOT NULL,
            currency TEXT DEFAULT 'EUR',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS wire_change_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wire_id INTEGER NOT NULL REFERENCES approved_wires(id),
            field_changed TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            reviewed_by TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
            review_notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            reviewed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor TEXT NOT NULL,
            fund_name TEXT NOT NULL,
            amount REAL NOT NULL,
            distribution_type TEXT DEFAULT 'return_of_capital'
                CHECK(distribution_type IN ('return_of_capital', 'income', 'gain', 'other')),
            value_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS nav_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            nav_amount REAL NOT NULL,
            reporting_date TEXT NOT NULL,
            source TEXT DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS gp_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            role TEXT DEFAULT 'Operations',
            email TEXT,
            phone TEXT,
            notes TEXT,
            primary_contact INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        # Migrate: add email tracking columns if missing (for existing databases)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(processed_calls)").fetchall()]
        if "email_sent" not in columns:
            conn.execute("ALTER TABLE processed_calls ADD COLUMN email_sent INTEGER NOT NULL DEFAULT 0")
        if "email_recipient" not in columns:
            conn.execute("ALTER TABLE processed_calls ADD COLUMN email_recipient TEXT")
        if "archive_path" not in columns:
            conn.execute("ALTER TABLE processed_calls ADD COLUMN archive_path TEXT")


def seed_from_excel(commitment_df, executed_df):
    """Populate the database from Excel data (only if tables are empty)."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM commitment_tracker").fetchone()[0]
        if count > 0:
            return  # Already seeded

        for _, row in commitment_df.iterrows():
            conn.execute(
                "INSERT INTO commitment_tracker (investor, fund_name, total_commitment, total_funded_ytd, remaining_open_commitment) VALUES (?, ?, ?, ?, ?)",
                (row["Investor"], row["Fund Name"], row["Total Commitment"],
                 row["Total Funded YTD"], row["Remaining Open Commitment"])
            )

        for _, row in executed_df.iterrows():
            conn.execute(
                "INSERT INTO executed_calls (investor, fund_name, amount, value_date, source) VALUES (?, ?, ?, ?, 'historical')",
                (row["Investor"], row["Fund Name"], row["Capital Call Amount Paid"], str(row["Value Date"]))
            )


def seed_default_users():
    """Create default users if none exist."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return
        defaults = [
            ("s.mueller", "Sebastian Mueller", "admin"),
            ("a.schmidt", "Anna Schmidt", "reviewer"),
            ("m.weber", "Max Weber", "reviewer"),
            ("l.fischer", "Laura Fischer", "analyst"),
            ("t.wagner", "Thomas Wagner", "analyst"),
        ]
        for username, display_name, role in defaults:
            conn.execute(
                "INSERT INTO users (username, display_name, role) VALUES (?, ?, ?)",
                (username, display_name, role)
            )


# ─── Query Functions ───

def get_commitment_tracker():
    """Return commitment tracker as list of dicts."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT investor, fund_name, total_commitment, total_funded_ytd, remaining_open_commitment FROM commitment_tracker ORDER BY investor, fund_name"
        ).fetchall()
        return [dict(r) for r in rows]


def get_commitment_for_fund(fund_name: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM commitment_tracker WHERE fund_name = ?", (fund_name,)
        ).fetchone()
        return dict(row) if row else None


def get_executed_calls():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT investor, fund_name, amount, value_date, source FROM executed_calls ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def get_processed_calls():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM processed_calls ORDER BY processed_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_processed_calls_filtered(
    date_from=None, date_to=None,
    statuses=None, funds=None, reviewer=None
) -> list[dict]:
    """Return processed calls with optional filters (AND logic)."""
    with get_db() as conn:
        query = "SELECT * FROM processed_calls WHERE 1=1"
        params = []
        if date_from:
            query += " AND processed_at >= ?"
            params.append(date_from.isoformat())
        if date_to:
            query += " AND processed_at <= ?"
            params.append(date_to.isoformat() + "T23:59:59")
        if statuses:
            placeholders = ",".join("?" * len(statuses))
            query += f" AND action IN ({placeholders})"
            params.extend(statuses)
        if funds:
            placeholders = ",".join("?" * len(funds))
            query += f" AND (fund_name_matched IN ({placeholders}) OR fund_name_extracted IN ({placeholders}))"
            params.extend(funds)
            params.extend(funds)
        if reviewer:
            placeholders = ",".join("?" * len(reviewer))
            query += f" AND reviewer IN ({placeholders})"
            params.extend(reviewer)
        query += " ORDER BY processed_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_unique_funds() -> list[str]:
    """Get distinct fund names from processed_calls for filter dropdown."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT fund_name_matched FROM processed_calls "
            "WHERE fund_name_matched IS NOT NULL "
            "UNION "
            "SELECT DISTINCT fund_name_extracted FROM processed_calls "
            "WHERE fund_name_extracted IS NOT NULL "
            "ORDER BY 1"
        ).fetchall()
        return [r[0] for r in rows]


def get_unique_reviewers() -> list[str]:
    """Get distinct reviewer names from processed_calls for filter dropdown."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT reviewer FROM processed_calls "
            "WHERE reviewer IS NOT NULL AND reviewer != '' "
            "ORDER BY reviewer"
        ).fetchall()
        return [r[0] for r in rows]


def get_users(role: str = None, active_only: bool = True):
    with get_db() as conn:
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        if active_only:
            query += " AND active = 1"
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY display_name"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_reviewers():
    """Get users who can serve as 2nd-eye reviewers (reviewer or admin role)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE role IN ('reviewer', 'admin') AND active = 1 ORDER BY display_name"
        ).fetchall()
        return [dict(r) for r in rows]


def export_commitment_tracker_df() -> pd.DataFrame:
    """Return commitment tracker as a formatted DataFrame for Excel export."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT investor, fund_name, total_commitment, total_funded_ytd, remaining_open_commitment "
            "FROM commitment_tracker ORDER BY investor, fund_name"
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows], columns=[
        "investor", "fund_name", "total_commitment", "total_funded_ytd", "remaining_open_commitment"
    ])
    df.columns = ["Investor", "Fund Name", "Total Commitment (EUR)", "Total Funded YTD (EUR)",
                   "Remaining Open Commitment (EUR)"]
    if not df.empty:
        df["% Funded"] = (df["Total Funded YTD (EUR)"] / df["Total Commitment (EUR)"] * 100).round(1)
    return df


def export_executed_calls_df() -> pd.DataFrame:
    """Return executed capital calls as a formatted DataFrame for Excel export."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT investor, fund_name, amount, value_date, source FROM executed_calls ORDER BY id"
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows], columns=[
        "investor", "fund_name", "amount", "value_date", "source"
    ])
    df.columns = ["Investor", "Fund Name", "Amount (EUR)", "Value Date", "Source"]
    return df


def export_audit_log_df() -> pd.DataFrame:
    """Return processed calls as a formatted DataFrame for Excel export."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT processed_at, fund_name_matched, fund_name_extracted, investor, amount, currency, "
            "overall_status, action, reviewer, commitment_passed, commitment_message, "
            "wire_passed, wire_message, filename "
            "FROM processed_calls ORDER BY processed_at DESC"
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows], columns=[
        "processed_at", "fund_name_matched", "fund_name_extracted", "investor", "amount", "currency",
        "overall_status", "action", "reviewer", "commitment_passed", "commitment_message",
        "wire_passed", "wire_message", "filename"
    ])
    df.columns = ["Timestamp", "Fund (Matched)", "Fund (Extracted)", "Investor", "Amount (EUR)",
                   "Currency", "Status", "Action", "Reviewer",
                   "Commitment Passed", "Commitment Message",
                   "Wire Passed", "Wire Message", "Filename"]
    return df


# ─── Mutation Functions ───

def execute_capital_call(validation: dict, reviewer_username: str, review_notes: str,
                         filename: str, email_body: str, archive_path: str = None) -> int:
    """Atomically: update commitment, add executed record, log processed call."""
    matched = validation["fund_name_matched"]
    amount = validation["amount"]

    with get_db() as conn:
        # Update commitment tracker
        conn.execute(
            "UPDATE commitment_tracker SET total_funded_ytd = total_funded_ytd + ?, remaining_open_commitment = remaining_open_commitment - ?, updated_at = datetime('now') WHERE fund_name = ?",
            (amount, amount, matched)
        )

        # Add executed call
        conn.execute(
            "INSERT INTO executed_calls (investor, fund_name, amount, value_date, source) VALUES (?, ?, ?, ?, 'sentinel')",
            (validation.get("investor", ""), matched, amount, datetime.now().strftime("%d.%m.%Y"))
        )

        # Log processed call
        cc = validation.get("commitment_check", {})
        wc = validation.get("wire_check", {})
        cursor = conn.execute(
            """INSERT INTO processed_calls
            (filename, fund_name_extracted, fund_name_matched, fund_match_score,
             investor, amount, currency, due_date, iban_extracted, iban_approved,
             commitment_passed, commitment_message, wire_passed, wire_message,
             overall_status, action, reviewer, review_notes, email_body, validation_json,
             archive_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, validation.get("fund_name_extracted"), matched,
             validation.get("fund_match_score"), validation.get("investor"),
             amount, validation.get("currency", "EUR"), validation.get("due_date"),
             wc.get("extracted_iban"), wc.get("approved_iban"),
             1 if cc.get("passed") else 0, cc.get("message"),
             1 if wc.get("passed") else 0, wc.get("message"),
             "APPROVED", "EXECUTED", reviewer_username, review_notes,
             email_body, json.dumps(validation, default=str),
             archive_path)
        )
        return cursor.lastrowid


def log_rejection(validation: dict, reviewer_username: str, review_notes: str,
                   filename: str, archive_path: str = None):
    """Log a rejected capital call."""
    cc = validation.get("commitment_check", {})
    wc = validation.get("wire_check", {})
    with get_db() as conn:
        conn.execute(
            """INSERT INTO processed_calls
            (filename, fund_name_extracted, fund_name_matched, fund_match_score,
             investor, amount, currency, due_date,
             commitment_passed, commitment_message, wire_passed, wire_message,
             overall_status, action, reviewer, review_notes, validation_json,
             archive_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, validation.get("fund_name_extracted"),
             validation.get("fund_name_matched"), validation.get("fund_match_score"),
             validation.get("investor"), validation.get("amount"),
             validation.get("currency", "EUR"), validation.get("due_date"),
             1 if cc.get("passed") else 0, cc.get("message"),
             1 if wc.get("passed") else 0, wc.get("message"),
             validation.get("overall_status", "UNKNOWN"), "REJECTED",
             reviewer_username, review_notes,
             json.dumps(validation, default=str),
             archive_path)
        )


def log_escalation(validation: dict, filename: str, archive_path: str = None):
    """Log an escalated capital call."""
    cc = validation.get("commitment_check", {})
    wc = validation.get("wire_check", {})
    with get_db() as conn:
        conn.execute(
            """INSERT INTO processed_calls
            (filename, fund_name_extracted, fund_name_matched, fund_match_score,
             investor, amount, currency, due_date,
             commitment_passed, commitment_message, wire_passed, wire_message,
             overall_status, action, validation_json, archive_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, validation.get("fund_name_extracted"),
             validation.get("fund_name_matched"), validation.get("fund_match_score"),
             validation.get("investor"), validation.get("amount"),
             validation.get("currency", "EUR"), validation.get("due_date"),
             1 if cc.get("passed") else 0, cc.get("message"),
             1 if wc.get("passed") else 0, wc.get("message"),
             validation.get("overall_status", "UNKNOWN"), "ESCALATED",
             json.dumps(validation, default=str),
             archive_path)
        )


def update_email_status(call_id: int, recipient: str):
    """Mark a processed call as having its confirmation email sent."""
    with get_db() as conn:
        conn.execute(
            "UPDATE processed_calls SET email_sent = 1, email_recipient = ? WHERE id = ?",
            (recipient, call_id)
        )


def is_file_already_processed(filename: str) -> bool:
    """Check if a PDF has already been processed (executed or rejected)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM processed_calls WHERE filename = ? AND action = 'EXECUTED'",
            (filename,)
        ).fetchone()
        return row[0] > 0


def find_potential_duplicates(fund_name: str, amount: float, due_date: str) -> list[dict]:
    """Find processed calls with matching fund, amount, and due date."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, filename, fund_name_matched, amount, due_date, action, processed_at
            FROM processed_calls
            WHERE fund_name_matched = ? AND amount = ? AND due_date = ?
            ORDER BY processed_at DESC
        """, (fund_name, amount, due_date)).fetchall()
        return [dict(r) for r in rows]


def find_fuzzy_duplicates(fund_name: str, amount: float) -> list[dict]:
    """Find processed calls with same fund and similar amount (within 1%)."""
    margin = amount * 0.01
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, filename, fund_name_matched, amount, due_date, action, processed_at
            FROM processed_calls
            WHERE fund_name_matched = ? AND amount BETWEEN ? AND ?
            ORDER BY processed_at DESC
        """, (fund_name, amount - margin, amount + margin)).fetchall()
        return [dict(r) for r in rows]


# ─── Commitment Amendment Functions ───

def create_commitment_amendment(fund_name: str, current_commitment: float,
                                current_remaining: float, requested_increase: float,
                                reason: str, capital_call_filename: str,
                                requested_by: str) -> int:
    """Create a new commitment amendment request."""
    new_commitment = current_commitment + requested_increase
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO commitment_amendments
            (fund_name, current_commitment, current_remaining, requested_increase,
             new_commitment, reason, capital_call_filename, requested_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fund_name, current_commitment, current_remaining, requested_increase,
             new_commitment, reason, capital_call_filename, requested_by)
        )
        return cursor.lastrowid


def approve_commitment_amendment(amendment_id: int, reviewed_by: str, notes: str = "") -> None:
    """Approve an amendment and update the commitment tracker."""
    with get_db() as conn:
        # Fetch the amendment details
        row = conn.execute(
            "SELECT * FROM commitment_amendments WHERE id = ? AND status = 'PENDING'",
            (amendment_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Amendment {amendment_id} not found or not pending.")

        increase = row["requested_increase"]
        fund = row["fund_name"]

        # Update the commitment tracker
        conn.execute(
            "UPDATE commitment_tracker SET total_commitment = total_commitment + ?, "
            "remaining_open_commitment = remaining_open_commitment + ?, "
            "updated_at = datetime('now') WHERE fund_name = ?",
            (increase, increase, fund)
        )

        # Mark amendment as approved
        conn.execute(
            "UPDATE commitment_amendments SET status = 'APPROVED', reviewed_by = ?, "
            "review_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
            (reviewed_by, notes, amendment_id)
        )


def reject_commitment_amendment(amendment_id: int, reviewed_by: str, notes: str = "") -> None:
    """Reject a commitment amendment request."""
    with get_db() as conn:
        conn.execute(
            "UPDATE commitment_amendments SET status = 'REJECTED', reviewed_by = ?, "
            "review_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
            (reviewed_by, notes, amendment_id)
        )


def get_pending_amendments() -> list[dict]:
    """Return all pending commitment amendments."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM commitment_amendments WHERE status = 'PENDING' ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_amendment_history() -> list[dict]:
    """Return all commitment amendments (all statuses) for audit."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM commitment_amendments ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Wire Instruction Management ───

def seed_wires_from_excel(wires_df):
    """Populate approved_wires from Excel data (only if table is empty)."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM approved_wires").fetchone()[0]
        if count > 0:
            return  # Already seeded

        for _, row in wires_df.iterrows():
            conn.execute(
                "INSERT INTO approved_wires (fund_name, beneficiary_bank, swift_bic, iban, currency) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["Fund Name"], row["Beneficiary Bank"], row.get("Swift/BIC", ""),
                 row["IBAN / Account Number"], row.get("Currency", "EUR"))
            )


def get_approved_wires() -> list[dict]:
    """Return all active approved wire instructions."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, fund_name, beneficiary_bank, swift_bic, iban, currency, "
            "created_at, updated_at FROM approved_wires WHERE active = 1 ORDER BY fund_name"
        ).fetchall()
        return [dict(r) for r in rows]


def get_approved_wires_df() -> pd.DataFrame:
    """Return approved wires as a DataFrame compatible with validation engine."""
    wires = get_approved_wires()
    if not wires:
        return pd.DataFrame(columns=["Fund Name", "Beneficiary Bank", "Swift/BIC",
                                      "IBAN / Account Number", "Currency"])
    df = pd.DataFrame(wires)
    df = df.rename(columns={
        "fund_name": "Fund Name",
        "beneficiary_bank": "Beneficiary Bank",
        "swift_bic": "Swift/BIC",
        "iban": "IBAN / Account Number",
        "currency": "Currency",
    })
    return df[["Fund Name", "Beneficiary Bank", "Swift/BIC", "IBAN / Account Number", "Currency"]]


def create_wire_change_request(wire_id: int, field: str, old_val: str,
                                new_val: str, reason: str, requested_by: str) -> int:
    """Submit a wire change request for review."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO wire_change_requests (wire_id, field_changed, old_value, new_value, reason, requested_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (wire_id, field, old_val, new_val, reason, requested_by)
        )
        return cursor.lastrowid


def approve_wire_change(change_id: int, reviewed_by: str, notes: str = "") -> None:
    """Approve a wire change request and apply it to the approved_wires table."""
    with get_db() as conn:
        # Fetch the change request
        change = conn.execute(
            "SELECT * FROM wire_change_requests WHERE id = ? AND status = 'PENDING'",
            (change_id,)
        ).fetchone()
        if not change:
            raise ValueError(f"Change request {change_id} not found or not pending")

        change = dict(change)

        # 4-eye: requester cannot approve own change
        if change["requested_by"] == reviewed_by:
            raise ValueError("Cannot approve your own change request (4-eye principle)")

        # Map field names to DB columns
        field_to_column = {
            "beneficiary_bank": "beneficiary_bank",
            "swift_bic": "swift_bic",
            "iban": "iban",
        }
        column = field_to_column.get(change["field_changed"])
        if not column:
            raise ValueError(f"Unknown field: {change['field_changed']}")

        # Apply the change to the wire record
        conn.execute(
            f"UPDATE approved_wires SET {column} = ?, updated_at = datetime('now') WHERE id = ?",
            (change["new_value"], change["wire_id"])
        )

        # Mark the request as approved
        conn.execute(
            "UPDATE wire_change_requests SET status = 'APPROVED', reviewed_by = ?, "
            "review_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
            (reviewed_by, notes, change_id)
        )


def reject_wire_change(change_id: int, reviewed_by: str, notes: str = "") -> None:
    """Reject a wire change request."""
    with get_db() as conn:
        change = conn.execute(
            "SELECT * FROM wire_change_requests WHERE id = ? AND status = 'PENDING'",
            (change_id,)
        ).fetchone()
        if not change:
            raise ValueError(f"Change request {change_id} not found or not pending")

        change = dict(change)

        # 4-eye: requester cannot reject own change either
        if change["requested_by"] == reviewed_by:
            raise ValueError("Cannot review your own change request (4-eye principle)")

        conn.execute(
            "UPDATE wire_change_requests SET status = 'REJECTED', reviewed_by = ?, "
            "review_notes = ?, reviewed_at = datetime('now') WHERE id = ?",
            (reviewed_by, notes, change_id)
        )


def get_pending_wire_changes() -> list[dict]:
    """Return all pending wire change requests with wire details."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT wcr.id, wcr.wire_id, wcr.field_changed, wcr.old_value, wcr.new_value, "
            "wcr.reason, wcr.requested_by, wcr.created_at, aw.fund_name "
            "FROM wire_change_requests wcr "
            "JOIN approved_wires aw ON wcr.wire_id = aw.id "
            "WHERE wcr.status = 'PENDING' "
            "ORDER BY wcr.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_wire_change_history() -> list[dict]:
    """Return all wire change requests (all statuses) for audit trail."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT wcr.id, wcr.wire_id, aw.fund_name, wcr.field_changed, "
            "wcr.old_value, wcr.new_value, wcr.reason, wcr.requested_by, "
            "wcr.reviewed_by, wcr.status, wcr.review_notes, "
            "wcr.created_at, wcr.reviewed_at "
            "FROM wire_change_requests wcr "
            "JOIN approved_wires aw ON wcr.wire_id = aw.id "
            "ORDER BY wcr.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# ─── GP Contact Directory ───

def seed_gp_contacts():
    """Populate gp_contacts with sample data (only if table is empty)."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM gp_contacts").fetchone()[0]
        if count > 0:
            return

        sample_contacts = [
            ("GT Partners IV Equity", "Hans Mueller", "Fund Operations", "h.mueller@gtpartners.com", "+49 69 1234 5678", "", 1),
            ("GT Partners IV Equity", "Katrin Braun", "Investor Relations", "k.braun@gtpartners.com", "+49 69 1234 5680", "", 0),
            ("GT Partners V Equity", "Claire Dubois", "Investor Relations", "c.dubois@gtpartners.com", "+41 44 987 6543", "", 1),
            ("GT Partners V Equity", "Hans Mueller", "Fund Operations", "h.mueller@gtpartners.com", "+49 69 1234 5678", "", 0),
            ("GT Partners VI Equity", "Hans Mueller", "Fund Operations", "h.mueller@gtpartners.com", "+49 69 1234 5678", "", 1),
            ("Parallax Fund Solutions - Buyout I", "James Wilson", "Treasury", "j.wilson@parallaxfunds.com", "+1 212 555 0100", "", 1),
            ("Parallax Fund Solutions - Buyout II", "James Wilson", "Treasury", "j.wilson@parallaxfunds.com", "+1 212 555 0100", "", 1),
            ("Parallax Fund Solutions - I", "Maria Santos", "Fund Operations", "m.santos@parallaxfunds.com", "+1 212 555 0101", "", 1),
            ("Parallax Fund Solutions - II", "Maria Santos", "Fund Operations", "m.santos@parallaxfunds.com", "+1 212 555 0101", "", 1),
            ("Global Infra Partners", "Thomas Richter", "Operations", "t.richter@globalinfra.com", "+44 20 7946 0958", "", 1),
            ("Global Infra Partners - Energy", "Thomas Richter", "Operations", "t.richter@globalinfra.com", "+44 20 7946 0958", "", 1),
            ("GIP - Energy", "Elena Rossi", "Investor Relations", "e.rossi@gipenergy.com", "+39 02 8765 4321", "", 1),
            ("Lattice Portfolio Advisors", "David Chen", "Fund Controller", "d.chen@latticeadvisors.com", "+1 415 555 0200", "", 1),
            ("Lattice Portfolio Advisors - US", "David Chen", "Fund Controller", "d.chen@latticeadvisors.com", "+1 415 555 0200", "", 1),
            ("Pillar Holdings", "Sophie Laurent", "Treasury Operations", "s.laurent@pillarholdings.com", "+352 26 1234 56", "", 1),
            ("Pillar Holdings II", "Sophie Laurent", "Treasury Operations", "s.laurent@pillarholdings.com", "+352 26 1234 56", "", 1),
            ("Tier One Aggregate Fund", "Marcus Weber", "Fund Administration", "m.weber@tieronefund.com", "+41 22 345 6789", "", 1),
            ("Vantage Point Partners II", "Alexandra Petrov", "Operations Manager", "a.petrov@vantagepointpartners.com", "+44 20 3456 7890", "", 1),
        ]
        for fund, name, role, email, phone, notes, primary in sample_contacts:
            conn.execute(
                "INSERT INTO gp_contacts (fund_name, contact_name, role, email, phone, notes, primary_contact) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fund, name, role, email, phone, notes, primary)
            )


def get_contacts_for_fund(fund_name: str) -> list[dict]:
    """Return active contacts for a specific fund, primary contacts first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM gp_contacts WHERE fund_name = ? AND active = 1 "
            "ORDER BY primary_contact DESC, contact_name",
            (fund_name,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_contacts() -> list[dict]:
    """Return all contacts (active and inactive), ordered by fund then name."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM gp_contacts ORDER BY fund_name, primary_contact DESC, contact_name"
        ).fetchall()
        return [dict(r) for r in rows]


def add_contact(fund_name: str, contact_name: str, role: str,
                email: str, phone: str, notes: str, primary_contact: int) -> int:
    """Add a new GP contact."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO gp_contacts (fund_name, contact_name, role, email, phone, notes, primary_contact) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fund_name, contact_name, role, email, phone, notes, primary_contact)
        )
        return cursor.lastrowid


def update_contact(contact_id: int, **fields) -> None:
    """Update fields on an existing contact."""
    allowed = {"fund_name", "contact_name", "role", "email", "phone", "notes", "primary_contact"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [contact_id]
    with get_db() as conn:
        conn.execute(f"UPDATE gp_contacts SET {set_clause} WHERE id = ?", values)


def deactivate_contact(contact_id: int) -> None:
    """Soft-delete a contact by marking it inactive."""
    with get_db() as conn:
        conn.execute("UPDATE gp_contacts SET active = 0 WHERE id = ?", (contact_id,))


# ─── Distributions & NAV ───

def seed_distributions_and_nav():
    """Populate distributions and nav_records with sample data (only if empty)."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM distributions").fetchone()[0]
        if count > 0:
            return

        distributions = [
            ("C - Fund Vintage 2010", "Global Infra Partners", 820000, "return_of_capital", "2024-03-15"),
            ("C - Fund Vintage 2010", "Global Infra Partners", 410000, "income", "2024-09-30"),
            ("C - Fund Vintage 2010", "Global Infra Partners", 615000, "gain", "2025-03-15"),
            ("C - Fund Vintage 2010", "GT Partners IV Equity", 1110000, "return_of_capital", "2024-06-30"),
            ("C - Fund Vintage 2010", "GT Partners IV Equity", 555000, "income", "2024-12-15"),
            ("C - Fund Vintage 2010", "GT Partners IV Equity", 832500, "gain", "2025-06-30"),
            ("C - Fund Vintage 2010", "Vantage Point Partners II", 445000, "return_of_capital", "2024-06-30"),
            ("C - Fund Vintage 2010", "Vantage Point Partners II", 222500, "gain", "2025-03-15"),
            ("C - Fund Vintage 2010", "Parallax Fund Solutions - Buyout I", 400000, "return_of_capital", "2024-09-30"),
            ("C - Fund Vintage 2010", "Parallax Fund Solutions - Buyout I", 200000, "income", "2025-03-15"),
            ("C - Fund Vintage 2015", "GT Partners V Equity", 650000, "return_of_capital", "2024-12-15"),
            ("C - Fund Vintage 2015", "GT Partners V Equity", 325000, "income", "2025-06-30"),
            ("C - Fund Vintage 2015", "Tier One Aggregate Fund", 700000, "return_of_capital", "2025-03-15"),
            ("C - Fund Vintage 2015", "Pillar Holdings", 600000, "return_of_capital", "2024-12-15"),
            ("C - Fund Vintage 2015", "Parallax Fund Solutions - Buyout II", 735000, "income", "2025-03-15"),
            ("C - Fund Vintage 2015", "Lattice Portfolio Advisors - US", 450000, "return_of_capital", "2025-06-30"),
            ("C- Fund Vintage 2019", "Global Infra Partners - Energy", 262500, "income", "2025-06-30"),
            ("C- Fund Vintage 2019", "GT Partners VI Equity", 260000, "return_of_capital", "2025-06-30"),
            ("C- Fund Vintage 2019", "Pillar Holdings II", 420000, "return_of_capital", "2025-03-15"),
        ]
        for investor, fund, amount, dtype, vdate in distributions:
            conn.execute(
                "INSERT INTO distributions (investor, fund_name, amount, distribution_type, value_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (investor, fund, amount, dtype, vdate)
            )

        nav_data = [
            ("Global Infra Partners", 9200000, "2025-12-31"),
            ("GT Partners IV Equity", 13500000, "2025-12-31"),
            ("Vantage Point Partners II", 5100000, "2025-12-31"),
            ("Parallax Fund Solutions - Buyout I", 4600000, "2025-12-31"),
            ("GT Partners V Equity", 15200000, "2025-12-31"),
            ("Tier One Aggregate Fund", 16500000, "2025-12-31"),
            ("Pillar Holdings", 13800000, "2025-12-31"),
            ("Parallax Fund Solutions - Buyout II", 17100000, "2025-12-31"),
            ("Lattice Portfolio Advisors - US", 10500000, "2025-12-31"),
            ("Global Infra Partners - Energy", 9800000, "2025-12-31"),
            ("GT Partners VI Equity", 6000000, "2025-12-31"),
            ("Pillar Holdings II", 15500000, "2025-12-31"),
        ]
        for fund, nav, rdate in nav_data:
            conn.execute(
                "INSERT INTO nav_records (fund_name, nav_amount, reporting_date) VALUES (?, ?, ?)",
                (fund, nav, rdate)
            )


def add_distribution(investor: str, fund_name: str, amount: float,
                     distribution_type: str, value_date: str, notes: str = "") -> int:
    """Record a new distribution."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO distributions (investor, fund_name, amount, distribution_type, value_date, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (investor, fund_name, amount, distribution_type, value_date, notes)
        )
        return cursor.lastrowid


def get_distributions() -> list[dict]:
    """Return all distributions ordered by date."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM distributions ORDER BY value_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_distributions_for_fund(fund_name: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM distributions WHERE fund_name = ? ORDER BY value_date DESC",
            (fund_name,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_nav_record(fund_name: str, nav_amount: float, reporting_date: str,
                   source: str = "manual") -> int:
    """Record a new NAV snapshot."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO nav_records (fund_name, nav_amount, reporting_date, source) "
            "VALUES (?, ?, ?, ?)",
            (fund_name, nav_amount, reporting_date, source)
        )
        return cursor.lastrowid


def get_nav_records() -> list[dict]:
    """Return all NAV records ordered by date."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM nav_records ORDER BY reporting_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_nav(fund_name: str) -> dict | None:
    """Return the most recent NAV record for a fund."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM nav_records WHERE fund_name = ? ORDER BY reporting_date DESC LIMIT 1",
            (fund_name,)
        ).fetchone()
        return dict(row) if row else None


def get_portfolio_summary() -> list[dict]:
    """Compute per-fund portfolio metrics: called, distributed, NAV, DPI, TVPI."""
    with get_db() as conn:
        funds = conn.execute(
            "SELECT DISTINCT fund_name, investor FROM commitment_tracker ORDER BY fund_name"
        ).fetchall()

        summary = []
        for f in funds:
            fund_name = f["fund_name"]
            investor = f["investor"]

            called_row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM executed_calls WHERE fund_name = ?",
                (fund_name,)
            ).fetchone()
            total_called = called_row["total"]

            dist_row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM distributions WHERE fund_name = ?",
                (fund_name,)
            ).fetchone()
            total_distributed = dist_row["total"]

            nav_row = conn.execute(
                "SELECT nav_amount FROM nav_records WHERE fund_name = ? ORDER BY reporting_date DESC LIMIT 1",
                (fund_name,)
            ).fetchone()
            latest_nav = nav_row["nav_amount"] if nav_row else 0

            dpi = total_distributed / total_called if total_called > 0 else 0
            tvpi = (total_distributed + latest_nav) / total_called if total_called > 0 else 0
            net_cash_flow = total_distributed - total_called

            summary.append({
                "investor": investor,
                "fund_name": fund_name,
                "total_called": total_called,
                "total_distributed": total_distributed,
                "latest_nav": latest_nav,
                "dpi": dpi,
                "tvpi": tvpi,
                "net_cash_flow": net_cash_flow,
            })
        return summary


def get_cumulative_cash_flows() -> list[dict]:
    """Return time-series of cumulative calls and distributions for charting."""
    with get_db() as conn:
        calls = conn.execute(
            "SELECT value_date as date, SUM(amount) as amount FROM executed_calls "
            "GROUP BY value_date ORDER BY value_date"
        ).fetchall()
        dists = conn.execute(
            "SELECT value_date as date, SUM(amount) as amount FROM distributions "
            "GROUP BY value_date ORDER BY value_date"
        ).fetchall()

    all_dates = set()
    call_by_date = {}
    dist_by_date = {}
    for r in calls:
        call_by_date[r["date"]] = r["amount"]
        all_dates.add(r["date"])
    for r in dists:
        dist_by_date[r["date"]] = r["amount"]
        all_dates.add(r["date"])

    sorted_dates = sorted(all_dates)
    cum_calls = 0
    cum_dists = 0
    result = []
    for d in sorted_dates:
        cum_calls += call_by_date.get(d, 0)
        cum_dists += dist_by_date.get(d, 0)
        result.append({
            "date": d,
            "cumulative_calls": cum_calls,
            "cumulative_distributions": cum_dists,
            "net_cash_flow": cum_dists - cum_calls,
        })
    return result
