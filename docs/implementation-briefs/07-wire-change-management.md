# Brief 07: Wire Instruction Change Management

## Priority: WAVE 2 | Parallel-Safe | Depends on Wave 1 merge

## Context

The "Approved Wire Instructions" page currently shows a read-only table loaded from Excel. In practice, wire instructions change (banks merge, accounts close, counterparties restructure). These changes are high-risk -- an unauthorized wire change is a primary fraud vector. The system needs a dual-authorization workflow for updating wire instructions.

## What to Build

1. **Wire Instructions stored in SQLite** (migrate from Excel-only)
2. **Propose Change** form for analysts to submit wire updates
3. **Review & Approve** workflow requiring a reviewer/admin to approve changes
4. **Change History** audit trail showing who changed what and when

## Implementation

### 1. New database tables in `database.py`

```sql
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
```

### 2. Seed from Excel

On first run, populate `approved_wires` from the Excel data (similar to how `commitment_tracker` is seeded).

### 3. Update validation engine

Modify `validation_engine.py` to optionally accept wire data from the database instead of the Excel DataFrame. The `run_full_validation()` function should check the DB-backed wires table.

### 4. New UI sections on "Approved Wire Instructions" page

**Current wires table** (from DB now, not Excel):
```python
wires = db.get_approved_wires()  # New function
st.dataframe(wires_df, ...)
```

**Propose Change form** (in an expander):
```python
with st.expander("Propose Wire Instruction Change"):
    wire_to_change = st.selectbox("Fund", [w["fund_name"] for w in wires])
    field = st.selectbox("Field to Change", ["beneficiary_bank", "swift_bic", "iban"])
    new_value = st.text_input("New Value")
    reason = st.text_area("Reason for Change (required)")
    if st.button("Submit Change Request"):
        db.create_wire_change_request(...)
```

**Pending changes** (visible to reviewers/admins only):
```python
if current_user["role"] in ("reviewer", "admin"):
    pending = db.get_pending_wire_changes()
    for change in pending:
        # Show old value, new value, reason, requested_by
        # Approve / Reject buttons
```

**Change history** (in a tab or expander):
```python
history = db.get_wire_change_history()
st.dataframe(history_df, ...)
```

### 5. Database functions to add

```python
def get_approved_wires() -> list[dict]: ...
def create_wire_change_request(wire_id, field, old_val, new_val, reason, requested_by): ...
def approve_wire_change(change_id, reviewed_by, notes=""): ...  # Also updates approved_wires
def reject_wire_change(change_id, reviewed_by, notes=""): ...
def get_pending_wire_changes() -> list[dict]: ...
def get_wire_change_history() -> list[dict]: ...
```

## Acceptance Criteria

- [ ] Wire instructions stored in SQLite, seeded from Excel on first run
- [ ] Analysts can propose wire changes with a reason
- [ ] Reviewers/admins see pending changes and can approve or reject
- [ ] Approved changes update the wire record immediately
- [ ] Full change history is visible and auditable
- [ ] Wire validation uses DB-backed data (not Excel)
- [ ] 4-eye principle enforced (requester cannot approve own change)
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (new tables, seed function, CRUD)
- `app.py` (Approved Wire Instructions page)
- `validation_engine.py` (accept DB-backed wire data)

## Do NOT

- Delete the Excel loading capability (keep as fallback/seed source)
- Allow direct wire edits without the change request workflow
