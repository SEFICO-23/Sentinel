# Brief 08: Commitment Amendment Workflow

## Priority: WAVE 2 | Parallel-Safe | Depends on Wave 1 merge

## Context

When a capital call exceeds the remaining open commitment (like Notice 1: EUR 5.6M vs EUR 3.9M remaining), the current system rejects it. In practice, the analyst should be able to initiate a commitment increase request to resolve this. The increase must be approved before the capital call can be retried.

## What to Build

1. **Amendment Request form** that appears when a call fails the commitment check
2. **Amendment Review** workflow for reviewers/admins
3. **Commitment update** on approval (increases the total commitment)
4. **Amendment history** for audit

## Implementation

### 1. New database table

```sql
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
```

### 2. Amendment trigger in Process Capital Call page

When `validation["overall_status"]` contains "OVER COMMITMENT", show an amendment form:
```python
if "COMMITMENT" in status:
    st.warning(f"Amount exceeds remaining commitment by EUR {cc['overage']:,.0f}")
    
    with st.expander("Request Commitment Increase"):
        st.markdown("Submit a commitment increase to resolve this capital call.")
        increase_amount = st.number_input(
            "Increase Amount (EUR)", 
            min_value=int(cc["overage"]),
            value=int(cc["overage"]),
            step=100000
        )
        reason = st.text_area("Justification", placeholder="e.g., Side letter amendment, GP notification of increased allocation...")
        if st.button("Submit Amendment Request"):
            db.create_commitment_amendment(
                fund_name=matched_fund,
                current_commitment=...,
                current_remaining=...,
                requested_increase=increase_amount,
                reason=reason,
                capital_call_filename=uploaded.name,
                requested_by=current_user["username"]
            )
            st.success("Amendment request submitted for review.")
```

### 3. Amendment review section

Add to the Dashboard or a new sidebar page "Amendments":
```python
if current_user["role"] in ("reviewer", "admin"):
    pending = db.get_pending_amendments()
    for amendment in pending:
        # Show fund, current commitment, requested increase, reason
        # Approve: updates commitment_tracker, sets status
        # Reject: sets status, adds notes
```

### 4. Database functions

```python
def create_commitment_amendment(fund_name, current_commitment, current_remaining, 
                                 requested_increase, reason, capital_call_filename, 
                                 requested_by): ...
def approve_commitment_amendment(amendment_id, reviewed_by, notes=""): ...
    # Must also UPDATE commitment_tracker SET total_commitment = total_commitment + increase,
    #   remaining_open_commitment = remaining_open_commitment + increase
def reject_commitment_amendment(amendment_id, reviewed_by, notes=""): ...
def get_pending_amendments() -> list[dict]: ...
def get_amendment_history() -> list[dict]: ...
```

### 5. Notification badge

Show a badge on the sidebar navigation when there are pending amendments:
```python
pending_count = len(db.get_pending_amendments())
if pending_count > 0:
    # Show count next to the page name
```

## Acceptance Criteria

- [ ] Amendment request form appears when a call exceeds remaining commitment
- [ ] Pre-fills with the minimum required increase amount
- [ ] Requires justification text
- [ ] Reviewers can approve or reject amendments
- [ ] Approved amendments update the commitment tracker immediately
- [ ] Amendment history is auditable
- [ ] After amendment approval, the same capital call PDF can be re-uploaded and will now pass
- [ ] 4-eye principle enforced (requester cannot approve own amendment)
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (new table, CRUD functions)
- `app.py` (Process Capital Call page + new review section)

## Do NOT

- Auto-approve amendments
- Allow amendments without a reason
