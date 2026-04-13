# Brief 12: Duplicate Detection

## Priority: WAVE 3 | Parallel-Safe | Depends on Wave 2 merge

## Context

Currently the system only prevents re-processing the exact same filename. But a duplicate capital call could arrive under a different filename (e.g., "Notice_3_v2.pdf" with the same fund/amount/date). Treasury needs to catch semantic duplicates, not just filename duplicates.

## What to Build

1. **Semantic duplicate check** based on (fund_name, amount, due_date) combination
2. **Warning display** when a potential duplicate is detected
3. **Override option** for legitimate re-submissions (with reason)

## Implementation

### 1. Add duplicate check to `database.py`

```python
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
```

### 2. Add fuzzy duplicate check

Also check for near-matches (same fund, similar amount within 1%):
```python
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
```

### 3. Show duplicate warning in `app.py`

After extraction and fund matching, before validation display:
```python
if validation["fund_name_matched"]:
    exact_dupes = db.find_potential_duplicates(
        validation["fund_name_matched"], validation["amount"], validation["due_date"]
    )
    fuzzy_dupes = db.find_fuzzy_duplicates(
        validation["fund_name_matched"], validation["amount"]
    )
    
    if exact_dupes:
        st.error(f"**DUPLICATE DETECTED:** An identical capital call (same fund, amount, due date) "
                 f"was already processed on {exact_dupes[0]['processed_at']} "
                 f"(file: {exact_dupes[0]['filename']}, status: {exact_dupes[0]['action']})")
    elif fuzzy_dupes:
        st.warning(f"**Potential duplicate:** A similar call for {validation['fund_name_matched']} "
                   f"with EUR {fuzzy_dupes[0]['amount']:,.0f} was processed on "
                   f"{fuzzy_dupes[0]['processed_at']}. Verify this is not a re-submission.")
```

### 4. Override with reason

If a duplicate is detected, require a reason to proceed:
```python
if duplicates_found:
    override_reason = st.text_input("Override reason (required to proceed)", 
                                      placeholder="e.g., Corrected notice, supersedes previous...")
    # Disable approval buttons until override reason is provided
```

## Acceptance Criteria

- [ ] Exact duplicates detected (same fund + amount + due date)
- [ ] Fuzzy duplicates detected (same fund + similar amount)
- [ ] Clear warning shown with details of the previous submission
- [ ] Override option with required reason
- [ ] Override reason stored in the audit trail
- [ ] Filename-based duplicate check still works as first gate
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (duplicate query functions)
- `app.py` (Process Capital Call page)

## Do NOT

- Block processing entirely (always allow override with reason)
- Change the processed_calls schema (store override reason in review_notes)
