# Brief 14: GP Contact Directory

## Priority: WAVE 3 | Parallel-Safe | Depends on Wave 2 merge

## Context

When a capital call fails validation (wire mismatch, over commitment), the treasury team needs to contact the GP's operations team. Currently there's no centralized contact directory -- analysts dig through emails to find the right person.

## What to Build

1. **Contacts table** linked to funds
2. **Contact display** on validation failure (who to call)
3. **Contact management** page for adding/editing contacts

## Implementation

### 1. New database table

```sql
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
```

### 2. Seed with sample contacts

```python
sample_contacts = [
    ("GT Partners IV Equity", "Hans Mueller", "Fund Operations", "h.mueller@gtpartners.com", "+49 69 1234 5678", "", 1),
    ("GT Partners V Equity", "Claire Dubois", "Investor Relations", "c.dubois@gtpartners.com", "+41 44 987 6543", "", 1),
    ("GT Partners VI Equity", "Hans Mueller", "Fund Operations", "h.mueller@gtpartners.com", "+49 69 1234 5678", "", 1),
    ("Parallax Fund Solutions - Buyout II", "James Wilson", "Treasury", "j.wilson@parallaxfunds.com", "+1 212 555 0100", "", 1),
    # ... etc for all funds
]
```

### 3. Contact display on validation failure

In the Process Capital Call page, when a validation fails:
```python
if not validation["commitment_check"]["passed"] or not validation["wire_check"]["passed"]:
    contacts = db.get_contacts_for_fund(validation["fund_name_matched"])
    if contacts:
        st.markdown('<div class="section-header">GP Contact for Escalation</div>', unsafe_allow_html=True)
        for contact in contacts:
            primary = " (Primary)" if contact["primary_contact"] else ""
            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom: 0.5rem;">
                <strong>{esc(contact['contact_name'])}</strong>{primary}<br>
                <span style="color: var(--text-secondary);">{esc(contact['role'])}</span><br>
                Email: {esc(contact['email'])} | Phone: {esc(contact['phone'])}
            </div>
            """, unsafe_allow_html=True)
```

### 4. Contact management page

Add a new sidebar page "GP Contacts" with:
- Table of all contacts grouped by fund
- Add contact form
- Edit/deactivate existing contacts

### 5. Database functions

```python
def get_contacts_for_fund(fund_name: str) -> list[dict]: ...
def get_all_contacts() -> list[dict]: ...
def add_contact(fund_name, name, role, email, phone, notes, primary): ...
def update_contact(contact_id, **fields): ...
def deactivate_contact(contact_id): ...
```

## Acceptance Criteria

- [ ] Contacts stored in database linked to fund names
- [ ] Primary contact flagged per fund
- [ ] Contacts shown on validation failure for quick escalation
- [ ] Contact management page with add/edit/deactivate
- [ ] Sample contacts seeded for demonstration
- [ ] Contacts searchable by fund name
- [ ] App still runs without errors: `python -m streamlit run app.py`

## Files to Modify

- `database.py` (new table, seed, CRUD)
- `app.py` (Process Capital Call page + new GP Contacts page)

## Do NOT

- Make contacts mandatory for processing
- Store sensitive data without escaping
